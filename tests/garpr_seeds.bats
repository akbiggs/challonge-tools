#!./libs/bats/bin/bats

load 'libs/bats-support/load'
load 'libs/bats-assert/load'

garpr_seeds="./garpr_seeds.py"

@test "$garpr_seeds fetches data and generates an equal-sized list of numbers" {
  run $garpr_seeds "NMW, Umarth, trock"
  assert_success
  assert_line --regexp "^\[[1-3], [1-3], [1-3]\]$"
}

@test "$garpr_seeds gives last seed to one unknown participant" {
  run $garpr_seeds "NMW, Umarth, trock, BLAHBLAHBLAHBLAH"
  assert_success
  assert_line --regexp "^\[[1-3], [1-3], [1-3], 4\]$"
}

@test "$garpr_seeds gives last seed in order of unknown participants" {
  run $garpr_seeds "NMW, Umarth, BLAHBLAH, trock, BLAHBLAHBLAHBLAH"
  assert_success
  assert_line --regexp "^\[[1-3], [1-3], 4, [1-3], 5\]$"
}

@test "$garpr_seeds ignores spelling case" {
  correct_case="$($garpr_seeds 'NMW, Umarth, trock')"
  weird_case="$($garpr_seeds 'nMw, UMARTH, tROCK')"
  assert_equal "$correct_case" "$weird_case"
}

@test "$garpr_seeds works with the Google MTV Region" {
  run $garpr_seeds --region=googlemtv "Eden, Bryan, NotGarPR, Admiral"
  assert_success
  assert_line --regexp "^\[[1-3], [1-3], 4, [1-3]\]$"
}
