#!./libs/bats/bin/bats

load 'libs/bats-support/load'
load 'libs/bats-assert/load'

create_amateur_bracket="./create_amateur_bracket.py"
challonge_config="./akbiggs_challonge.ini"

@test "$create_amateur_bracket figures out the amateur bracket successfully" {
  run $create_amateur_bracket mtvmelee73 --config_file=$challonge_config
}

