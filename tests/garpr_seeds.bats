#!./libs/bats/bin/bats

load 'libs/bats-support/load'
load 'libs/bats-assert/load'

garpr_seeds="./garpr_seeds.py"

@test "$garpr_seeds fetches data and generates an equal-sized list of numbers" {
  run $garpr_seeds "Eden, gaR, Admiral"
  assert_success
  assert_line --regexp "^\[[1-3], [1-3], [1-3]\]$"
}

@test "$garpr_seeds gives last seed to one unknown participant" {
  run $garpr_seeds "Eden, gaR, Admiral, BLAHBLAHBLAHBLAH"
  assert_success
  assert_line --regexp "^\[[1-3], [1-3], [1-3], 4\]$"
}

@test "$garpr_seeds gives last seed in order of unknown participants" {
  run $garpr_seeds "Eden, gaR, BLAHBLAH, Admiral, BLAHBLAHBLAHBLAH"
  assert_success
  assert_line --regexp "^\[[1-3], [1-3], 4, [1-3], 5\]$"
}

@test "$garpr_seeds ignores spelling case" {
  correct_case="$($garpr_seeds 'Eden, gaR, Admiral')"
  weird_case="$($garpr_seeds 'eDen, Gar, aDmIrAl')"
  assert_equal "$correct_case" "$weird_case"
}
