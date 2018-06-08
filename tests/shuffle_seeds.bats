#!./libs/bats/bin/bats

load 'libs/bats-support/load'
load 'libs/bats-assert/load'

shuffle_seeds="./shuffle_seeds.py"
seed=1500

@test "$shuffle_seeds shuffles a number of participants" {
  run $shuffle_seeds 9 --seed=$seed
  assert_success
  assert_line "[1, 2, 3, 4, 6, 5, 7, 8, 9]"
}

@test "$shuffle_seeds returns empty list for zero participants" {
  run $shuffle_seeds 0
  assert_success
  assert_line "[]"
}

@test "$shuffle_seeds shuffles a list of participant names" {
  run $shuffle_seeds "Neal, Bryan, Paragon, gaR, Admiral Lightning Bolt, Eden" --seed=$seed
  assert_success
  assert_line "['Neal', 'Bryan', 'Paragon', 'gaR', 'Eden', 'Admiral Lightning Bolt']"
}

@test "$shuffle_seeds needs one argument" {
  run $shuffle_seeds
  assert_failure
}
