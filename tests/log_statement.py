import unittest

import log_recommender.log_statement as ls

__author__ = 'hlib'

text = '''
                String prefix = (String) e.get_value();
\t\t\t\tif (uri != null && prefix != null) {
                    uri2prefix.put(uri, prefix.trim());
                    count++;}}
            LOGGER.info("Added [" + count + "] namespace entries resulting in [" + uri2prefix.size()
                    + "] distinct entries");
}}    /**
     * @return the exportDefaultValues
     */
'''

text2 = '''
    h++k
'''

# print(filter_out_1_and_2_char_tokens(split_to_key_words_and_identifiers(text)))
print(text)
print(ls.spl_verbose(text))

if __name__ == '__main__':
    unittest.main()
