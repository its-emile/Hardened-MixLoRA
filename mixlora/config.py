import copy
from dataclasses import dataclass
from typing import Dict, List

import torch
from transformers.activations import ACT2FN


@dataclass
class AdapterConfig:
    adapter_name_: str = None
    hidden_size_: int = None
    model_type_: str = None
    dtype_: torch.dtype = None


@dataclass
class LoraConfig(AdapterConfig):
    # Weight-Decomposed Low-Rank Adaptation
    use_dora_: bool = False
    # Rank-Stabilized LoRA
    # sets the adapter scaling factor to `alpha/math.sqrt(r)`
    use_rslora_: bool = False
    # can be original or gaussian
    lora_init_: str = "original"
    lora_r_: int = None
    lora_alpha_: int = None
    lora_dropout_: float = None
    target_modules_: Dict[str, bool] = None

    def check(self) -> "LoraConfig":
        assert isinstance(self.use_dora_, bool)
        assert isinstance(self.use_rslora_, bool)
        assert isinstance(self.lora_init_, str) and self.lora_init_ in [
            "original",
            "gaussian",
        ]
        assert isinstance(self.lora_r_, int) and self.lora_r_ > 0
        assert isinstance(self.lora_alpha_, int) and self.lora_alpha_ > 0
        assert isinstance(self.lora_dropout_, float) and self.lora_dropout_ >= 0
        assert isinstance(self.target_modules_, Dict)
        for key, value in self.target_modules_.items():
            assert isinstance(key, str) and len(key) > 0
            assert isinstance(value, bool)

        return self

    def from_config(self, config: Dict[str, any]) -> "LoraConfig":
        self.use_dora_ = config.get("use_dora", False)
        self.use_rslora_ = config.get("use_rslora", False)
        self.lora_init_ = config.get("lora_init", "original")
        self.lora_r_ = config["r"]
        self.lora_alpha_ = config["lora_alpha"]
        self.lora_dropout_ = config["lora_dropout"]
        self.target_modules_ = {
            # LLaMA names
            "q_proj": False,
            "k_proj": False,
            "v_proj": False,
            "o_proj": False,
            "gate_proj": False,
            "down_proj": False,
            "up_proj": False,
        }
        if isinstance(config["target_modules"], List):
            for target in config["target_modules"]:
                if target in self.target_modules_:
                    self.target_modules_[target] = True
        elif isinstance(config["target_modules"], Dict):
            for target, value in config["target_modules"].items():
                if target in self.target_modules_:
                    self.target_modules_[target] = value
        else:
            raise ValueError("broken config item: target_modules")

        return self

    def export(self) -> Dict[str, any]:
        config = {}
        if self.use_dora_:
            config["use_dora"] = True
        if self.use_rslora_:
            config["use_rslora"] = True
        config["bias"] = "none"
        config["peft_type"] = "LORA"
        config["r"] = self.lora_r_
        config["lora_alpha"] = self.lora_alpha_
        config["lora_dropout"] = self.lora_dropout_
        tgt_list = []
        for target, value in self.target_modules_.items():
            if value:
                tgt_list.append(target)
        config["target_modules"] = tgt_list

        return config


available_routing_strategies = ["mixtral"]


@dataclass
class MixLoraConfig(LoraConfig):
    # expert lora
    expert_config_: LoraConfig = None
    # router config
    router_aux_loss_coef_: float = None
    router_init_range_: float = None
    routing_strategy_: str = None
    jitter_noise_: float = None
    router_loss_: bool = True
    num_experts_: int = None
    act_fn_: str = None
    # mixtral config
    top_k_: int = None

    def check(self) -> "MixLoraConfig":
        super().check()
        if self.expert_config_ is not None:
            self.expert_config_.check()
        assert (
            isinstance(self.router_aux_loss_coef_, float)
            and self.router_aux_loss_coef_ >= 0
        )
        assert (
            isinstance(self.router_init_range_, float) and self.router_init_range_ >= 0
        )
        assert (
            isinstance(self.routing_strategy_, str)
            and self.routing_strategy_ in available_routing_strategies
        )
        assert isinstance(self.jitter_noise_, float) and self.jitter_noise_ >= 0
        assert isinstance(self.router_loss_, bool)
        assert isinstance(self.num_experts_, int) and self.num_experts_ > 0
        assert self.act_fn_ is None or (
            isinstance(self.act_fn_, str) and self.act_fn_ in ACT2FN
        )
        if self.routing_strategy_ == "mixtral":
            assert isinstance(self.top_k_, int) and self.top_k_ > 0
        else:
            raise NotImplementedError()

        return self

    def from_config(self, config: Dict[str, any]) -> "MixLoraConfig":
        assert config["peft_type"] == "MIXLORA"
        super().from_config(config)
        if "expert_lora" in config:
            expert_config = copy.deepcopy(config)
            expert_config.update(config["expert_lora"])
            self.expert_config_ = LoraConfig().from_config(expert_config)
        self.router_aux_loss_coef_ = config.get(
            "router_aux_loss_coef", 0.001
        )  # for training
        self.routing_strategy_ = config["routing_strategy"]
        self.router_loss_ = config.get("router_loss", True)
        self.num_experts_ = config["num_experts"]
        # silu for mixtral or gelu_new for switch transformers
        # left blank to automatically use the original act_fn of FFN
        self.act_fn_ = config.get("act_fn", None)
        if self.routing_strategy_ == "mixtral":
            self.router_init_range_ = config.get("router_init_range", 0.02)
            self.jitter_noise_ = config.get("jitter_noise", 0.0)
            self.top_k_ = config.get("top_k", 2)
        else:
            raise NotImplementedError()

        return self

    def export(self) -> Dict[str, any]:
        config = super().export()
        config["peft_type"] = "MIXLORA"
        if self.expert_config_ is not None:
            expert_config = self.expert_config_.export()
            expert_config.pop("peft_type")
            expert_config.pop("target_modules")
            config["expert_lora"] = expert_config
        config["routing_strategy"] = self.routing_strategy_
        config["num_experts"] = self.num_experts_
        if self.act_fn_ is not None:
            config["act_fn"] = self.act_fn_
        if self.routing_strategy_ == "mixtral":
            config["top_k"] = self.top_k_
        else:
            raise NotImplementedError()

        return config

    def expert_config(self, expert_idx: int) -> LoraConfig:
        if self.expert_config_ is None:
            config = copy.deepcopy(super())
        else:
            config = copy.deepcopy(self.expert_config_)
        config.adapter_name = f"moe.{self.adapter_name}.experts.{expert_idx}"
        return config
