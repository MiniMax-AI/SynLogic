# SynLogic

This repo contains the resources (**Code**, **Data**) for the paper "SynLogic: Synthesizing Verifiable Reasoning Data at Scale for Learning Logical Reasoning and Beyond"

SynLogic: is a comprehensive logical reasoning data synthesis framework and dataset, encompasssing **35** different tasks. The presence of SynLogic allow reinforcement learning LLMs on these tasks, substantial improves LLM logical reasoning ability, where our zero-RL models match DeeepSeek-R1-Distill-32B on KOR-Bench, and surpassing it on BBEH.

## News
- :fire: [05/2025] We are excited to release the resources for the paper "SynLogic: Synthesizing Verifiable Reasoning Data at Scale for Learning Logical Reasoning and Beyond"

## Overview
This repository aims to enhance Large Language Model (LLM) logical reasoning capabilities through a collection of logical reasoning tasks paired with:
1. **Adjustable Difficulty** - Difficulty parameters when generating tasks data
2. **Task Generator** - Code for the data generation
3. **Task Verifier** - Verifier for the specific task


## Quick Start (For Arrow Maze)
1. Install this package using ```pip install -r reqruiements.txt``` before running the following command.
2. Run game generation example using ```games/tasks/arrow_maze/run.sh``` 
or
```python scripts/arrow_maze.py --num_of_data 1000 --width 5 --height 5 --arrow_fill_rate_min 0.3 --arrow_fill_rate_max 0.9```, where we can control the difficulty by these parameters like `width` `height`  `arrow_fill_rate_min` `arrow_fill_rate_max`.



## :rocket: Resources

### Datasets
| Dataset Name | Description | Link |
|:------------:|:------------|:----:|
| **SynLogic** | Training dataset | [🤗 HuggingFace]() |

