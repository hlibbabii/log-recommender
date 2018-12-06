import unittest

from logrec.langmodel.utils import beautify_text

text_boundaries = '''
public `c `C ar ti fact `c request `c builder w` `c ar ti fact w` ( final `C string `c co or d in ate s w` ) { `c set `c ar ti fact w` ( new `c `C default `c ar ti fact w` ( `c co or d in ate s w` ) ) ; return this ; } public `c `C ar ti fact `c request `c builder w` `c ar ti fact w` ( final `C string `c group `c id w` , final `C string `c ar ti fact `c id w` , final `C string version , final `C string `c exten sion w` , final `C string `c class i fier w` ) { `c set `c ar ti fact w` ( new `c `C default `c ar ti fact w` ( `c group `c id w` , `c ar ti fact `c id w` , `c class i fier w` , `c exten sion w` , version ) ) ; return this ; } public `c `C ar ti fact `c request `c builder w` `c ar ti fact w` ( final `C string `c group `c id w` , final `C string `c ar ti fact `c id w` , final `C string version , final `C string `c exten sion w` ) { `c set `c ar ti fact w` ( new `c `C default `c ar ti fact w` ( `c group `c id w` , `c ar ti fact `c id w` , `c exten sion w` , version ) ) ; return this ; } public `c `C ar ti fact `c request `c builder w` `c ar ti fact w` ( final `C string `c group `c id w` , final `C string `c ar ti fact `c id w` , final `C string version ) { return `c ar ti fact w` ( `c group `c id w` , `c ar ti fact `c id w` , version , " `c j ar w` " ) ; } public `c `C ar ti fact `c request `c builder w` `c re pos it ory w` ( final `c `C remo te `c re pos it ory w` . . . `c re pos it ori es w` ) { for ( `c `C remo te `c re pos it ory w` `c re pos it ory w` : `c re pos it ori es w` ) { `c add `c re pos it ory w` ( `c re pos it ory w` ) ; } return this ; } } ``
/* * `C copyright ( c ) `c 200 9 w` - `c 20 11 w` `c `C son at y pe w` , `C inc . * `C all `c right s w` `c re ser ved w` . `C this program and the `c ac comp any ing w` `c mat er i als w` * are `c ma de w` `c avai lable w` under the terms of the `C eclipse `C public `C license `c v `c 1 w` . 0 * and `C apache `C license `c v `c 2 w` . 0 which `c ac comp an i es w` this `c distribu tion w` . * `C the `C eclipse `C public `C license is `c avai lable w` at * http : // www . eclipse . org / legal / `c ep l w` - `c v `c 10 w` . html * `C the `C apache `C license `c v `c 2 w` . 0 is `c avai lable w` at * http : // www . apache . org / licenses / `Cs license - 2 . 0 . html * `C you may `c e le ct w` to `c re dist ribute w` this code under either of `c the se w` licenses . */ package org . `c son at y pe w` . `c s is u w` . `c m av en w` . `c b rid ge w` . `c sup port w` ; import java . util . `c `C array `c list w` ; import java . util . `C collection ; import org . apache . `c m av en w` . model . `c `C re pos it ory w` ; import org . `c son at y pe w` . `c a e ther w` . `c re pos it ory w` . `c `C remo te `c re pos it ory w` ; import org . `c son at y pe w` . `c a e ther w` . `c re pos it ory w` . `c `C re pos it ory `c po lic y w` ; /* * * `c `Cs to do w`
'''

text_boundaries_expected = '''
public ArtifactRequestBuilder artifact ( final String coordinates ) { setArtifact ( new DefaultArtifact ( coordinates ) ) ; return this ; } public ArtifactRequestBuilder artifact ( final String groupId , final String artifactId , final String version , final String extension , final String classifier ) { setArtifact ( new DefaultArtifact ( groupId , artifactId , classifier , extension , version ) ) ; return this ; } public ArtifactRequestBuilder artifact ( final String groupId , final String artifactId , final String version , final String extension ) { setArtifact ( new DefaultArtifact ( groupId , artifactId , extension , version ) ) ; return this ; } public ArtifactRequestBuilder artifact ( final String groupId , final String artifactId , final String version ) { return artifact ( groupId , artifactId , version , " jar " ) ; } public ArtifactRequestBuilder repository ( final RemoteRepository...repositories ) { for ( RemoteRepository repository : repositories ) { addRepository ( repository ) ; } return this ; } } 


/* * Copyright ( c ) 2009 - 2011 Sonatype , Inc.* All rights reserved.This program and the accompanying materials * are made available under the terms of the Eclipse Public License v1.0 * and Apache License v2.0 which accompanies this distribution.* The Eclipse Public License is available at * http : // www.eclipse.org / legal / epl - v10.html * The Apache License v2.0 is available at * http : // www.apache.org / licenses / LICENSE - 2.0.html * You may elect to redistribute this code under either of these licenses.*/ package org.sonatype.sisu.maven.bridge.support ; import java.util.ArrayList ; import java.util.Collection ; import org.apache.maven.model.Repository ; import org.sonatype.aether.repository.RemoteRepository ; import org.sonatype.aether.repository.RepositoryPolicy ; /* * * TODO
'''


# text_separators


class UtilTest(unittest.TestCase):
    def test_beautify_1(self):
        text_boundaries1 = '`c `C ar ti fact `c req uest `c build er `c cl ass w`'

        actual = beautify_text(text_boundaries1)

        expected = "ArtifactRequestBuilderClass"

        self.assertEqual(expected, actual)

    def test_beautify_2(self):
        text_boundaries1 = '`c `Cs to do w`'

        actual = beautify_text(text_boundaries1)

        expected = "TODO"

        self.assertEqual(expected, actual)

    def test_beautify_3(self):
        text_boundaries1 = '`c TO DO w`'

        actual = beautify_text(text_boundaries1)

        expected = "TODO"

        self.assertEqual(expected, actual)

    def test_beautify_boundaries(self):
        actual = beautify_text(text_boundaries)

        self.assertEqual(text_boundaries_expected, actual)


if __name__ == '__main__':
    unittest.main()
