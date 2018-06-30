pp_params = {
    'preprocessors': [
        "lines_to_one_lines_with_newlines",
        "replace_4whitespaces_with_tabs",
        "spl_verbose",
        "split_line_canel_case",
        "split_line_underscore",
        # "merge_tabs",
        "java.strip_off_string_literals",
        "java.strip_off_multiline_comments",
        "java.strip_off_one_line_comments",
        "java.strip_off_number_literals",
        # "java.strip_off_identifiers"
        "newline_and_tab_remover",
        "to_string_repr"
    ],
    'more_lines_ignore': 2000
}