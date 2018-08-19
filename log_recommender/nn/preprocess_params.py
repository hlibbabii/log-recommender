pp_params = {
    'preprocessors': [
        "general.lines_to_one_lines_with_newlines",

        "java.process_numeric_literals",

        "general.replace_4whitespaces_with_tabs",
        "general.spl_verbose",


        "split.camel_case",
        "split.underscore",
        "split.with_numbers",
        # "legacy.merge_tabs",

        "java.strip_off_string_literals",
        "java.strip_off_multiline_comments",
        "java.strip_off_one_line_comments",
        "repr.to_repr",

        # "java.strip_off_identifiers"
        # "same_case_split.split",
        "general.to_human_readable"
    ],
    'more_lines_ignore': 5000
}