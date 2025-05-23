# SynLogic


## Quick Start (For Game of 24)
1. Install this package using ```pip install -r reqruiements.txt``` before running the following command.
2. Run game generation example using ```games/tasks/game_of_24/run.sh```.


## Overview
This repository aims to enhance Large Language Model (LLM) logical reasoning capabilities through a collection of triplets consisting of:
1. **Queries** - Carefully crafted prompts that require logical reasoning
2. **Answers** - Only the final solutions to queries
3. **Unhackable Checkers** - Executable code that programmatically verifies the correctness of answers

Each sample in our dataset contains all three components, enabling robust validation of reasoning capabilities.

## Data Collection Methods


### Game Generation
- Design diverse reasoning challenges through structured rule-based "games" (broadly defined to include any problem-solving scenarios)
- Ensure comprehensive coverage of reasoning types by incorporating a wide variety of game formats.
- Build automated systems to:
  - Generate scalable game instances with adjustable difficulty levels
  - Implement rigorous verification mechanisms to ensure answer correctness



