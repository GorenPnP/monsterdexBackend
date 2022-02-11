# monsterdexBackend

## dev
start dev server with `$ ./start_dev.sh`


## deploy to Heroku

`$ git push heroku <local branchname>:main`.

_Note: `heroku` is registered as remote next to origin_

### file explanations of those needed by Heroku
| | |
|-|-|
| requirements.txt | all external dependencies. Need to be installed before executing the project |
| runtime.txt | specifies python version |
| Procfile | run on start of instance/dyno to run the BE |