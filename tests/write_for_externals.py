from logrec.dataprep.preprocessors import apply_preprocessors
from logrec.dataprep.preprocessors.preprocessor_list import pp_params
from logrec.dataprep.preprocessors.general import from_file

__author__ = 'hlib'

import unittest


class PreprocessTest(unittest.TestCase):
    @unittest.skip("outdated")  # TODO update!!!
    def test_process_full_identifiers(self):
        inp = [
'public class WR3223Activator implements BundleActivator { // 6_89',
'    private static Logger logger = LoggerFactory.getLogger(WR3223Activator.class);',
'    @Override 0 1 2',
'    public void start(BundleContext context) throws Exception {',
'        logger.debug("WR3223 Binding has been started.");',
'    }',
'',
'    @Override',
'    public void stop(BundleContext context) throws Exception {',
'    /*    context = null;',
'    */    logger.debug("WR3223 Binding has been stopped 5677788888 .");'
]

        expected = '''public class wr3223activator implements bundle <identifiersep> activator { <comment> \n \t1 private static logger logger = logger <identifiersep> factory . get <identifiersep> logger ( wr3223activator . class ) ; \n \t1 @ override 0 1 <number_literal> \n \t1 public void start ( bundle <identifiersep> context context ) throws exception { \n \t2 logger . debug ( <string_literal> ) ; \n \t1 } \n \n \t1 @ override \n \t1 public void stop ( bundle <identifiersep> context context ) throws exception { \n \t1 <comment> \t1 logger . debug ( <string_literal> ) ; \n <ect>'''

        actual = apply_preprocessors(from_file(inp), pp_params["preprocessors"], {'interesting_context_words': []})

        self.assertEqual(repr(expected)[1:-1] + "\n", actual)


if __name__ == '__main__':
    unittest.main()
