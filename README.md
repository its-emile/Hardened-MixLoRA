# Hardened-MixLoRA: protecting LLM-based applications with instruction hierarchy in LoRA-based Mixture of Experts

Based on [MixLORA](https://arxiv.org/html/2404.15159v1) and [Instruction Hierarchy](https://arxiv.org/abs/2404.13208)
<div align="left"><img src="https://raw.githubusercontent.com/TUDB-Labs/MixLoRA/main/assets/MixLoRA.png" width=60%"></div>

We use MixLoRA, which constructs fine-tuning using a sparse MoE model based on LoRA. The figure above shows the architecture of the MixLoRA transformer block. MixLoRA inserts multiple LoRA-based experts within the feed-forward network block of a frozen pre-trained dense model and employs a commonly used top-k router. 

We fine-tune and evaluate [meta-llama/Llama-2-7b-hf](https://huggingface.co/meta-llama/Llama-2-7b-hf) on an instruction-hierarchy version MoE-PEFT, in which only privileged instructions control the router, with an objective to freeze the router once unprivileged contents are present (aka untrusted data).


## Acknowledgements
this work is based on MixLoRA, for whose authors we are particularly grateful.
```bibtex
@misc{li2024mixlora,
      title={MixLoRA: Enhancing Large Language Models Fine-Tuning with LoRA-based Mixture of Experts}, 
      author={Dengchun Li and Yingzi Ma and Naizheng Wang and Zhengmao Ye and Zhiyuan Cheng and Yinghao Tang and Yan Zhang and Lei Duan and Jie Zuo and Cal Yang and Mingjie Tang},
      year={2024},
      eprint={2404.15159},
      archivePrefix={arXiv},
      primaryClass={cs.CL}
}

@misc{alpaca-mixlora-7b,
  author = {Dengchun Li and Yingzi Ma and Naizheng Wang and Zhengmao Ye and Zhiyuan Cheng and Yinghao Tang and Yan Zhang and Lei Duan and Jie Zuo and Cal Yang and Mingjie Tang},
  title = {MixLoRA LoRA MoE adapter based on AlpacaCleaned dataset and LLaMA-2-7B base model},
  year = {2024},
  publisher = {HuggingFace Hub},
  howpublished = {\url{https://huggingface.co/TUDB-Labs/alpaca-mixlora-7b}},
}
```

## Copyright
Copyright © 2023-2024 All Rights Reserved.

MixLoRA, MoE-PEFT and the weights of alpaca-mixlora-7b are licensed under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0).

```
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
