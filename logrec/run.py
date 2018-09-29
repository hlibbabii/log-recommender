from paramtaskrun.paramtaskrun import Project

Project('../config.json', '../prev_runs.pkl').run(
    '../tunable-params.json', '../non-tunable-params.json', []
)