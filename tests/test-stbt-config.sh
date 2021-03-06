# Run with ./run-tests.sh

test_that_stbt_config_reads_from_STBT_CONFIG_FILE() {
    cat >test-stbt.conf <<-EOF
	[global]
	another_test_key = this is a test value
	EOF
    export STBT_CONFIG_FILE=$PWD/test-stbt.conf &&
    [ "$(stbt config global.another_test_key)" = "this is a test value" ]
}

test_that_stbt_config_searches_in_specified_section() {
    [ "$(stbt config special.test_key)" = "not the global value" ]
}

test_that_stbt_config_returns_failure_on_key_not_found() {
    ! stbt config global.no_such_key &&
    ! stbt config no_such_section.test_key &&
    ! stbt config not_special.section
}
