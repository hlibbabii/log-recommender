pp_params = {
    'preprocessors': [
        "general.lines_to_one_lines_with_newlines",

        "java.process_numeric_literals",

        "general.replace_4whitespaces_with_tabs",
        "general.spl_verbose",


        "split.camel_case",
        "split.underscore",
        "split.with_numbers",
        "split.same_case",
        # "legacy.merge_tabs",

        "java.process_comments_and_str_literals",
        # "noneng.mark", # this should be applied after all splittings

        # "java.strip_off_identifiers"
        # "general.to_human_readable"
    ]
}