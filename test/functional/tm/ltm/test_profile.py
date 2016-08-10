# Copyright 2015-2106 F5 Networks Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import copy
from distutils.version import LooseVersion
from f5.bigip.mixins import UnsupportedTmosVersion
from pprint import pprint as pp
pp(__file__)
import pytest

TESTDESCRIPTION = "TESTDESCRIPTION"


# Helper class to limit code repetition
class HelperTest(object):
    def __init__(self, collection_name):
        self.partition = 'Common'
        self.lowered = collection_name.lower()
        self.test_name = 'test.' + self.urielementname()

    def urielementname(self):
        if self.lowered[-2:] == '_s':
            endind = 2
        else:
            endind = 1
        return self.lowered[:-endind]

    def setup_test(self, request, bigip, **kwargs):
        resourcecollection =\
            getattr(getattr(getattr(bigip, 'ltm'), 'profile'), self.lowered)
        resource = getattr(resourcecollection, self.urielementname())
        if resource.exists(name=self.test_name, partition=self.partition):
            resource.load(
                name=self.test_name, partition=self.partition).delete()
        created = resource.create(name=self.test_name,
                                  partition=self.partition,
                                  **kwargs)
        request.addfinalizer(created.delete)
        return created, resourcecollection

    def test_MCURDL(self, request, bigip, **kwargs):

        # Testing create
        profile1, rescollection = self.setup_test(request, bigip, **kwargs)
        assert profile1.name == self.test_name

        # Testing update
        profile1.description = TESTDESCRIPTION
        profile1.update()
        if hasattr(profile1, 'description'):
            assert profile1.description == TESTDESCRIPTION

        # Testing refresh
        profile1.description = ''
        profile1.refresh()
        if hasattr(profile1, 'description'):
            assert profile1.description == TESTDESCRIPTION

        # Testing modify
        meta_data = profile1.__dict__.pop('_meta_data')
        start_dict = copy.deepcopy(profile1.__dict__)
        profile1.__dict__['_meta_data'] = meta_data
        profile1.modify(description='MODIFIED')
        for k, v in profile1.__dict__.items():
            if k != 'description' and\
               k != 'generation' and\
               k != '_meta_data' and\
               k != 'secret':
                assert getattr(profile1, k) == start_dict[k]
            elif k == 'description':
                assert getattr(profile1, 'description') == 'MODIFIED'

        if '~Common~test.client_ssl' in profile1.selfLink:
            assert profile1.secureRenegotiation == 'require'
            meta_data = profile1.__dict__.pop('_meta_data')
            start_dict = copy.deepcopy(profile1.__dict__)
            profile1.__dict__['_meta_data'] = meta_data
            profile1.modify(secureRenegotiation='require-strict')
            for k, v in profile1.__dict__.items():
                if k != 'secureRenegotiation'\
                        and k != 'generation'\
                        and k != '_meta_data':
                    assert getattr(profile1, k) == start_dict[k]
                elif k == 'secureRenegotiation':
                    assert profile1.secureRenegotiation == 'require-strict'
            profile1.modify(secureRenegotiation='require')
        # Testing load
        p2 = getattr(rescollection, self.urielementname())
        profile2 = p2.load(partition=self.partition, name=self.test_name)
        assert profile1.selfLink == profile2.selfLink

    def test_MCURDL_Adapt(self, request, bigip):

        # Testing create
        profile1, rescollection = self.setup_test(request, bigip)
        assert profile1.name == self.test_name

        # Testing update
        profile1.timeout = 10
        profile1.update()
        assert profile1.timeout == 10

        # Testing refresh
        profile1.timeout = 0
        profile1.refresh()
        assert profile1.timeout == 10

        # Testing load
        p2 = getattr(rescollection, self.urielementname())
        profile2 = p2.load(partition=self.partition, name=self.test_name)
        assert profile1.selfLink == profile2.selfLink

# Begin Analytics tests
# Sub-collection setup function


def setup_test_subc(request, bigip):
    def teardown():
        if prf_alert.exists(name='test_alert'):
            prf_alert.delete()
        if prf_traffic.exists(name='test_traf_cap'):
            prf_traffic.delete()

    avr = HelperTest('Analytics_s')
    avrstr, avrhc1 = avr.setup_test(request, bigip)
    del avrstr
    prf_alert = avrhc1.alerts_s.alerts
    prf_alert.create(name='test_alert', threshold=200)
    prf_traffic = avrhc1.traffic_captures.traffic_capture.create(
        name='test_traf_cap')
    request.addfinalizer(teardown)
    return prf_alert, prf_traffic, avrhc1


@pytest.mark.skipif(True, reason='this depends on an optional module')
class TestAnalytics(object):
    def test_MCURDL(self, request, bigip):
        avr = HelperTest('Analytics_s')
        avr.test_MCURDL(request, bigip)


@pytest.mark.skipif(True, reason='this depends on an optional module')
class TestAnalyticsSubCol(object):
    def test_MCURDL(self, request, bigip):

        # Testing create and delete
        alert1, traffic1, avrhc1 = setup_test_subc(request, bigip)
        assert alert1.name == 'test_alert'
        assert traffic1.name == 'test_traf_cap'

        # Testing update
        alert1.threshold = 250
        alert1.update()
        assert alert1.threshold == 250
        traffic1.requestCapturedParts = 'headers'
        traffic1.update()
        assert traffic1.requestCapturedParts == 'headers'

        # Testing refresh
        alert1.threshold = 200
        alert1.refresh()
        assert alert1.threshold == 250
        traffic1.requestCapturedParts = 'none'
        traffic1.refresh()
        assert traffic1.requestCapturedParts == 'headers'

        # Testing load
        alert2 = avrhc1.alerts_s.alerts.load(name='test_alert')
        assert alert1.name == alert2.name
        traffic2 = avrhc1.traffic_captures.traffic_capture.load(
            name='test_traf_cap')
        assert traffic1.name == traffic2.name


# End Analytics tests

# Begin Certificate Authority tests


class TestCertificateAuthority(object):
    def test_MCURDL(self, request, bigip):
        ca = HelperTest('Certificate_Authoritys')
        ca.test_MCURDL(request, bigip)


# End Certificate Authority tests

# Begin Classification tests


class TestClassification(object):
    def test_RUL(self, request, bigip):

        # Load test
        klass1 = bigip.ltm.profile.classifications.classification.\
            load(name='classification')

        # Update test
        klass1.description = TESTDESCRIPTION
        klass1.update()
        assert klass1.description == TESTDESCRIPTION

        # Refresh test
        klass1.description = 'ICHANGEDIT'
        klass1.refresh()
        assert klass1.description == TESTDESCRIPTION


# End Classification tests

# Begin ClientLdap tests


class TestClientLdap(object):
    @pytest.mark.skipif(
        LooseVersion(pytest.config.getoption('--release'))
        < LooseVersion('11.6.0'),
        reason='This collection exists on 11.6.0 or greater.'
    )
    def test_MCURDL_11_6_and_greater(self, request, bigip):
        ldap = HelperTest('Client_Ldaps')
        ldap.test_MCURDL(request, bigip)

    @pytest.mark.skipif(
        LooseVersion(pytest.config.getoption('--release'))
        >= LooseVersion('11.6.0'),
        reason='This collection does not exist on 11.5.4 or less.'
    )
    def test_MCURDL_11_5_4_and_less(self, request, bigip):
        ldap = HelperTest('Client_Ldaps')
        with pytest.raises(UnsupportedTmosVersion) as ex:
            ldap.test_MCURDL(request, bigip)
        assert 'minimum TMOS version in which this resource *is* supported ' \
            'is 11.6.0' in ex.value.message

# End ClientLdap tests

# Begin ClientSSL tests


class TestClientSsl(object):
    def test_MCURDL(self, request, bigip):
        cssl = HelperTest('Client_Ssls')
        cssl.test_MCURDL(request, bigip)


# End ClientSSL tests

# Begin Dhcpv4 tests


class TestDhcpv4(object):
    @pytest.mark.skipif(
        LooseVersion(pytest.config.getoption('--release'))
        < LooseVersion('11.6.0'),
        reason='This collection exists on 11.6.0 or greater.'
    )
    def test_MCURDL_11_6_and_greater(self, request, bigip):
        dhcpv4 = HelperTest('Dhcpv4s')
        dhcpv4.test_MCURDL(request, bigip)

    @pytest.mark.skipif(
        LooseVersion(pytest.config.getoption('--release'))
        >= LooseVersion('11.6.0'),
        reason='This collection does not exist on 11.5.4 or less.'
    )
    def test_MCURDL_11_5_4_and_less(self, request, bigip):
        dhcpv4 = HelperTest('Dhcpv4s')
        with pytest.raises(UnsupportedTmosVersion) as ex:
            dhcpv4.test_MCURDL(request, bigip)
        assert 'minimum TMOS version in which this resource *is* supported ' \
            'is 11.6.0' in ex.value.message


# End Dhcpv4 tests

# Begin Dhcpv6 tests


class TestDhcpv6(object):
    @pytest.mark.skipif(
        LooseVersion(pytest.config.getoption('--release'))
        < LooseVersion('11.6.0'),
        reason='This collection exists on 11.6.0 or greater.'
    )
    def test_MCURDL_11_6_and_greater(self, request, bigip):
        dhcpv6 = HelperTest('Dhcpv6s')
        dhcpv6.test_MCURDL(request, bigip)

    @pytest.mark.skipif(
        LooseVersion(pytest.config.getoption('--release'))
        >= LooseVersion('11.6.0'),
        reason='This collection does not exist on 11.5.4 or less.'
    )
    def test_MCURDL_11_5_4_and_less(self, request, bigip):
        dhcpv4 = HelperTest('Dhcpv6s')
        with pytest.raises(UnsupportedTmosVersion) as ex:
            dhcpv4.test_MCURDL(request, bigip)
        assert 'minimum TMOS version in which this resource *is* supported ' \
            'is 11.6.0' in ex.value.message
# End Dhcpv6 tests

# Begin Diameter tests


class TestDiameter(object):
    def test_MCURDL(self, request, bigip):
        diameter = HelperTest('Diameters')
        diameter.test_MCURDL(request, bigip)


# End Diameter tests

# Begin Dns tests


class TestDns(object):
    def test_MCURDL(self, request, bigip):
        dns = HelperTest('Dns_s')
        dns.test_MCURDL(request, bigip)


# End Dns tests

# Begin Dns Logging tests


class TestDnsLogging(object):
    def test_MCURDL(self, request, bigip):
        dnslog = HelperTest('Dns_Loggings')

        # Testing create

        dns1, dnshc = dnslog.setup_test(
            request, bigip,
            logPublisher='/Common/local-db-publisher')
        assert dns1.name == 'test.dns_logging'
        del dnshc

        # Testing update
        assert dns1.enableQueryLogging == 'yes'
        dns1.enableQueryLogging = 'no'
        dns1.update()
        assert dns1.enableQueryLogging == 'no'

        # Testing refresh
        dns1.enableQueryLogging = 'yes'
        dns1.refresh()
        assert dns1.enableQueryLogging == 'no'

        # Testing load
        dns2 = bigip.ltm.profile.dns_loggings.dns_logging.load(
            partition='Common', name='test.dns_logging')
        assert dns1.selfLink == dns2.selfLink

# End Dns Logging test

# Begin FastHttp tests


class TestFastHttp(object):
    def test_MCURDL(self, request, bigip):
        fasthttp = HelperTest('Fasthttps')
        fasthttp.test_MCURDL(request, bigip)


# End FastHttp tests

# Begin FastL4 tests


class TestFastL4(object):
    def test_MCURDL(self, request, bigip):
        fastl4 = HelperTest('Fastl4s')
        fastl4.test_MCURDL(request, bigip)


# End FastL4 tests

# Begin Fix tests


class TestFix(object):
    def test_MCURDL(self, request, bigip):
        fix = HelperTest('Fixs')

        # Testing create

        fix1, fixc = fix.setup_test(request, bigip)
        assert fix1.name == 'test.fix'
        del fixc

        # Testing update
        assert fix1.quickParsing == 'false'
        fix1.quickParsing = 'true'
        fix1.update()
        assert fix1.quickParsing == 'true'

        # Testing refresh
        fix1.quickParsing = 'false'
        fix1.refresh()
        assert fix1.quickParsing == 'true'

        # Testing load
        fix2 = bigip.ltm.profile.fixs.fix.load(
            partition='Common', name='test.fix')
        assert fix1.selfLink == fix2.selfLink


# End Fix tests

# Begin FTP tests


class TestFtp(object):
    def test_MCURDL(self, request, bigip):
        ftp = HelperTest('Ftps')
        ftp.test_MCURDL(request, bigip)


# End FTP tests

# Begin GTP tests


class TestGtp(object):
    @pytest.mark.skipif(
        LooseVersion(pytest.config.getoption('--release'))
        < LooseVersion('11.6.0'),
        reason='This collection exists on 11.6.0 or greater.'
    )
    def test_MCURDL_11_6_and_greater(self, request, bigip):
        gtp = HelperTest('Gtps')
        gtp.test_MCURDL(request, bigip)

    @pytest.mark.skipif(
        LooseVersion(pytest.config.getoption('--release'))
        >= LooseVersion('11.6.0'),
        reason='This collection does not exist on 11.5.4 or less.'
    )
    def test_MCURDL_11_5_4_and_less(self, request, bigip):
        dhcpv4 = HelperTest('Gtps')
        with pytest.raises(UnsupportedTmosVersion) as ex:
            dhcpv4.test_MCURDL(request, bigip)
        assert 'minimum TMOS version in which this resource *is* supported ' \
            'is 11.6.0' in ex.value.message


# End GTP tests

# Begin HTML tests


class TestHtml(object):
    def test_MCURDL(self, request, bigip):
        html = HelperTest('Htmls')
        html.test_MCURDL(request, bigip)


# End HTML tests

# Begin HTTP tests


class TestHttp(object):
    def test_MCURDL(self, request, bigip):
        http = HelperTest('Https')
        http.test_MCURDL(request, bigip)


# End HTTP tests

# Begin HTTP Compression tests


class TestHttpCompress(object):
    def test_MCURDL(self, request, bigip):
        httpc = HelperTest('Http_Compressions')
        httpc.test_MCURDL(request, bigip)


# End HTTP Compression tests

# Begin HTTP tests


class TestHttp2(object):
    @pytest.mark.skipif(
        LooseVersion(pytest.config.getoption('--release'))
        < LooseVersion('11.6.0'),
        reason='This collection exists on 11.6.0 or greater.'
    )
    def test_MCURDL_11_6_and_greater(self, request, bigip):
        http2 = HelperTest('Http2s')
        http2.test_MCURDL(request, bigip)

    @pytest.mark.skipif(
        LooseVersion(pytest.config.getoption('--release'))
        >= LooseVersion('11.6.0'),
        reason='This collection does not exist on 11.5.4 or less.'
    )
    def test_MCURDL_11_5_4_and_less(self, request, bigip):
        dhcpv4 = HelperTest('Http2s')
        with pytest.raises(UnsupportedTmosVersion) as ex:
            dhcpv4.test_MCURDL(request, bigip)
        assert 'minimum TMOS version in which this resource *is* supported ' \
            'is 11.6.0' in ex.value.message


# End HTTP tests

# Begin ICAP tests


class TestIcap(object):
    def test_MCURDL(self, request, bigip):
        icap = HelperTest('Icaps')

        # Test Create
        icap1, icapc = icap.setup_test(request, bigip)
        assert icap1.name == 'test.icap'

        # Test Update
        icap1.previewLength = 100
        icap1.update()
        assert icap1.previewLength == 100

        # Test Refresh
        icap1.previewLength = 50
        icap1.refresh()
        assert icap1.previewLength == 100

        # Test Load
        icap2 = bigip.ltm.profile.icaps.icap.load(
            name='test.icap', partition='Common')
        assert icap1.selfLink == icap2.selfLink


# End ICAP tests

# Begin IIOP tests

@pytest.mark.skipif(pytest.config.getoption('--release') != '12.0.0',
                    reason='Needs v12 TMOS to pass')
class TestIiop(object):
    def test_MCURDL(self, request, bigip):
        iiop = HelperTest('Iiops')
        iiop.test_MCURDL(request, bigip)


# End IIOP tests

# Begin Ipother tests


class TestIother(object):
    def test_MCURDL(self, request, bigip):
        ipoth = HelperTest('Ipothers')
        ipoth.test_MCURDL(request, bigip)


# End Ipother tests

# Begin Mblb tests


class TestMblb(object):
    def test_MCURDL(self, request, bigip):
        mblb = HelperTest('Mblbs')
        mblb.test_MCURDL(request, bigip)


# End Mblb tests

# Begin Mssql tests

class TestMssql(object):
    def test_MCURDL(self, request, bigip):
        mssql = HelperTest('Mssqls')

        # Testing create

        mssql1, mssqlc = mssql.setup_test(request, bigip)
        assert mssql1.name == 'test.mssql'
        del mssqlc

        # Testing update
        assert mssql1.userCanWriteByDefault == 'true'
        mssql1.userCanWriteByDefault = 'false'
        mssql1.update()
        assert mssql1.userCanWriteByDefault == 'false'

        # Testing refresh
        mssql1.userCanWriteByDefault = 'true'
        mssql1.refresh()
        assert mssql1.userCanWriteByDefault == 'false'

        # Testing load
        mssql2 = bigip.ltm.profile.mssqls.mssql.load(
            partition='Common', name='test.mssql')
        assert mssql1.selfLink == mssql2.selfLink


# End Mssql tests

# Begin Ntlm tests


class TestNtlm(object):
    def test_MCURDL(self, request, bigip):
        ntlm = HelperTest('Ntlms')
        ntlm.test_MCURDL(request, bigip)


# End Ntlm tests

# Begin Ocsp Stapling Params tests

def setup_dns_resolver(request, bigip, name):
    def teardown():
        if dns_res.exists(name=name):
            dns_res.delete()
    request.addfinalizer(teardown)
    dns_res = bigip.net.dns_resolvers.dns_resolver.create(name=name)
    return dns_res


class TestOcspStaplingParams(object):
    @pytest.mark.skipif(
        LooseVersion(pytest.config.getoption('--release'))
        < LooseVersion('11.6.0'),
        reason='This collection exists on 11.6.0 or greater.'
    )
    def test_MCURDL_11_6_and_greater(self, request, bigip):

        # Setup DNS resolver as prerequisite
        dns = setup_dns_resolver(request, bigip, 'test_resolv')

        # Test CURDL
        ocsp = HelperTest('Ocsp_Stapling_Params_s')

        # Testing create
        ocsp1, ocsphc = ocsp.setup_test(
            request, bigip, dnsResolver=dns.name,
            trustedCa='/Common/ca-bundle.crt',
            useProxyServer='disabled')

        pp(ocsp1.raw)
        assert ocsp1.name == 'test.ocsp_stapling_params'
        del ocsphc

        # Testing update
        ocsp1.cacheErrorTimeout = 3000
        ocsp1.update()
        assert ocsp1.cacheErrorTimeout == 3000

        # Testing refresh
        ocsp1.cacheErrorTimeout = 30
        ocsp1.refresh()
        assert ocsp1.cacheErrorTimeout == 3000

        # Testing load
        ocsp_params = bigip.ltm.profile.ocsp_stapling_params_s
        ocsp2 = ocsp_params.ocsp_stapling_params.load(
            partition='Common', name='test.ocsp_stapling_params')

        assert ocsp1.selfLink == ocsp2.selfLink

    @pytest.mark.skipif(
        LooseVersion(pytest.config.getoption('--release'))
        >= LooseVersion('11.6.0'),
        reason='This collection does not exist on 11.5.4 or less.'
    )
    def test_MCURDL_11_6_and_less(self, request, bigip):

        # Setup DNS resolver as prerequisite
        dns = setup_dns_resolver(request, bigip, 'test_resolv')

        # Test CURDL
        ocsp = HelperTest('Ocsp_Stapling_Params_s')

        # Testing create
        with pytest.raises(UnsupportedTmosVersion) as ex:
            ocsp.setup_test(
                request, bigip, dnsResolver=dns.name,
                trustedCa='/Common/ca-bundle.crt',
                useProxyServer='disabled'
            )
        assert 'minimum TMOS version in which this resource *is* supported ' \
            'is 11.6.0' in ex.value.message

# End Ocsp Stapling Params tests

# Begin Oneconnect tests


class TestOneConnect(object):
    def test_MCURDL(self, request, bigip):
        onec = HelperTest('One_Connects')
        onec.test_MCURDL(request, bigip)


# End Oneconnect tests

# Begin Pcp tests


@pytest.mark.skipif(True, reason='this depends on an optional module')
class TestPcp(object):
    def test_MCURDL(self, request, bigip):
        pcp = HelperTest('Pcps')
        pcp.test_MCURDL(request, bigip)


# End Pcp tests

# Begin Pptp tests


class TestPptp(object):
    def test_MCURDL(self, request, bigip):
        pptp = HelperTest('Pptps')
        pptp.test_MCURDL(request, bigip)


# End Pptp tests

# Begin Qoe tests


class TestQoe(object):
    def test_MCURDL(self, request, bigip):
        qoe = HelperTest('Qoes')

        # Testing create

        qoe1, qoec = qoe.setup_test(request, bigip)
        assert qoe1.name == 'test.qoe'
        del qoec

        # Testing update
        assert qoe1.video == 'false'
        qoe1.video = 'true'
        qoe1.update()
        assert qoe1.video == 'true'

        # Testing refresh
        qoe1.video = 'false'
        qoe1.refresh()
        assert qoe1.video == 'true'

        # Testing load
        qoe2 = bigip.ltm.profile.qoes.qoe.load(
            partition='Common', name='test.qoe')
        assert qoe1.selfLink == qoe2.selfLink


# End Qoe tests

# Begin Radius tests


class TestRadius(object):
    def test_MCURDL(self, request, bigip):
        radius = HelperTest('Radius_s')
        radius.test_MCURDL(request, bigip)


# End Radius tests

# Begin Request Adapt tests


class TestRequestAdapt(object):
    def test_MCURDL(self, request, bigip):
        rq_adp = HelperTest('Request_Adapts')
        rq_adp.test_MCURDL_Adapt(request, bigip)


# End Request Adapt tests

# Begin Request Log tests


class TestRequestLog(object):
    def test_MCURDL(self, request, bigip):
        rq_log = HelperTest('Request_Logs')
        rq_log.test_MCURDL(request, bigip)


# End Request Log tests

# Begin Response Adapt tests


class TestResponseAdapt(object):
    def test_MCURDL(self, request, bigip):
        res_adp = HelperTest('Response_Adapts')
        res_adp.test_MCURDL_Adapt(request, bigip)


# End Response Adapt tests

# Begin Rewrite tests
# Sub-collection setup function


def setup_test_uri(request, bigip):
    def teardown():
        if uri1.exists(name='test.uri'):
            uri1.delete()

    rewrite = HelperTest('Rewrites')
    url_rw, rewrite_str = rewrite.setup_test(
        request, bigip, rewriteMode='uri-translation')
    del rewrite_str
    client = {'host': 'example.com', 'path': '/', 'scheme': 'http'}
    server = {'host': 'instance.com', 'path': '/', 'scheme': 'http'}
    uri1 = url_rw.uri_rules_s.uri_rules.create(name='test.uri',
                                               type='request',
                                               client=client,
                                               server=server)
    request.addfinalizer(teardown)
    return uri1, url_rw


class TestRewrite(object):
    def test_MCURDL_rewrite(self, request, bigip):

        # Test Create
        rewrite = HelperTest('Rewrites')
        rewrite1, rewrite_str = \
            rewrite.setup_test(request, bigip)
        del rewrite_str
        assert rewrite1.name == 'test.rewrite'

        # Test update
        rewrite1.clientCachingType = 'no-cache'
        rewrite1.update()
        assert rewrite1.clientCachingType == 'no-cache'

        # Test refresh
        rewrite1.splitTunneling = 'true'
        rewrite1.refresh()
        assert rewrite1.splitTunneling == 'false'

        # Test load
        rewrite2 = bigip.ltm.profile.rewrites.rewrite.load(name='test.rewrite',
                                                           partition='Common')
        assert rewrite1.selfLink == rewrite2.selfLink


class TestUriRulesSubCol(object):
    def test_MCURDL(self, request, bigip):

        # Test Create
        uri1, uri_rw = setup_test_uri(request, bigip)
        assert uri1.name == 'test.uri'

        # Test Update
        client = {'host': 'sample.com',
                  'path': '/', 'scheme': 'https'}
        uri1.client = client
        uri1.update()
        assert uri1.client == {'host': 'sample.com',
                               'path': '/', 'scheme': 'https'}

        # Test Refresh
        client = {'host': 'changed.com',
                  'path': '/', 'scheme': 'http'}
        uri1.client = client
        uri1.refresh()
        assert uri1.client == {'host': 'sample.com',
                               'path': '/', 'scheme': 'https'}

        # Test Load
        uri2 = uri_rw.uri_rules_s.uri_rules.load(name='test.uri')
        assert uri1.selfLink == uri2.selfLink


# End Rewrite tests

# Begin Rstps tests


class TestRstps(object):
    def test_MCURDL(self, request, bigip):
        rstps = HelperTest('Rtsps')
        rstps.test_MCURDL(request, bigip)


# End Rstps tests

# Begin Sctps tests


class TestSctps(object):
    def test_MCURDL(self, request, bigip):
        sctps = HelperTest('Sctps')
        sctps.test_MCURDL(request, bigip)


# End Sctps tests

# Begin Server Ldap tests


class TestServerLdap(object):
    @pytest.mark.skipif(
        LooseVersion(pytest.config.getoption('--release'))
        < LooseVersion('11.6.0'),
        reason='This collection exists on 11.6.0 or greater.'
    )
    def test_MCURDL_11_6_and_greater(self, request, bigip):
        sldap = HelperTest('Server_Ldaps')
        sldap.test_MCURDL(request, bigip)

    @pytest.mark.skipif(
        LooseVersion(pytest.config.getoption('--release'))
        >= LooseVersion('11.6.0'),
        reason='This collection does not exist on 11.5.4 or less.'
    )
    def test_MCURDL_11_5_4_and_less(self, request, bigip):
        dhcpv4 = HelperTest('Server_Ldaps')
        with pytest.raises(UnsupportedTmosVersion) as ex:
            dhcpv4.test_MCURDL(request, bigip)
        assert 'minimum TMOS version in which this resource *is* supported ' \
            'is 11.6.0' in ex.value.message


# End Server Ldap tests

# Begin Server Ssl tests


class TestServerSsl(object):
    def test_MCURDL(self, request, bigip):
        sssl = HelperTest('Server_Ssls')
        sssl.test_MCURDL(request, bigip)


# End Server Ldap tests

# Begin Sip tests


class TestSip(object):
    def test_MCURDL(self, request, bigip):
        sip = HelperTest('Sips')
        sip.test_MCURDL(request, bigip)


# End Sip tests

# Begin Smtp tests


class TestSmtp(object):
    @pytest.mark.skipif(
        LooseVersion(pytest.config.getoption('--release'))
        < LooseVersion('11.6.0'),
        reason='This collection exists on 11.6.0 or greater.'
    )
    def test_MCURDL_11_6_and_greater(self, request, bigip):
        smtp = HelperTest('Smtps')
        smtp.test_MCURDL(request, bigip)

    @pytest.mark.skipif(
        LooseVersion(pytest.config.getoption('--release'))
        >= LooseVersion('11.6.0'),
        reason='This collection does not exist on 11.5.4 or less.'
    )
    def test_MCURDL_11_5_4_and_less(self, request, bigip):
        dhcpv4 = HelperTest('Smtps')
        with pytest.raises(UnsupportedTmosVersion) as ex:
            dhcpv4.test_MCURDL(request, bigip)
        assert 'minimum TMOS version in which this resource *is* supported ' \
            'is 11.6.0' in ex.value.message


# End Smtp tests

# Begin Smtps tests


class TestSmtps(object):
    def test_MCURDL(self, request, bigip):
        smtps = HelperTest('Smtps_s')
        smtps.test_MCURDL(request, bigip)


# End Smtps tests

# Begin Sock tests


class TestSock(object):
    def test_MCURDL(self, request, bigip):

        dns = setup_dns_resolver(request, bigip,
                                 'test_resolv')
        socks = HelperTest('Socks_s')
        socks.test_MCURDL(request, bigip,
                          dnsResolver=dns.name)


# End Sock tests

# Begin Spdy tests


class TestSpdy(object):
    def test_MCURDL(self, request, bigip):
        spdy = HelperTest('Spdys')
        spdy.test_MCURDL(request, bigip)


# End Spdy tests

# Begin Statistics tests


class TestStatistics(object):
    def test_MCURDL(self, request, bigip):
        stat = HelperTest('Statistics_s')
        stat.test_MCURDL(request, bigip)


# End Statistics tests

# Begin Stream tests


class TestStream(object):
    def test_MCURDL(self, request, bigip):
        stream = HelperTest('Streams')
        stream.test_MCURDL(request, bigip)


# End Stream tests

# Begin Tcp tests


class TestTcp(object):
    def test_MCURDL(self, request, bigip):
        testcp = HelperTest('Tcps')
        testcp.test_MCURDL(request, bigip)


# End Tcp tests

# Begin Tftp tests

@pytest.mark.skipif(pytest.config.getoption('--release') != '12.0.0',
                    reason='Needs v12 TMOS to pass')
class TestTftp(object):
    def test_MCURDL(self, request, bigip):
        tftp = HelperTest('Tftps')
        tftp.test_MCURDL(request, bigip)


# End Tftp tests

# Begin Udp tests


class TestUdp(object):
    def test_MCURDL(self, request, bigip):
        tesudp = HelperTest('Udps')
        tesudp.test_MCURDL(request, bigip)


# End Udp tests


# Begin WebAcceleration tests


class TestWebAcceleration(object):
    def test_MCURDL(self, request, bigip):
        wa = HelperTest('Web_Accelerations')

        # Test Create
        wa1, wapc = wa.setup_test(request, bigip)
        assert wa1.name == 'test.web_acceleration'

        # Test Update
        wa1.cacheAgingRate = 5
        wa1.update()
        assert wa1.cacheAgingRate == 5

        # Test Refresh
        wa1.cacheAgingRate = 10
        wa1.refresh()
        assert wa1.cacheAgingRate == 5

        # Test Load
        wa2 = bigip.ltm.profile.web_accelerations.web_acceleration.load(
            name='test.web_acceleration', partition='Common')
        assert wa1.cacheAgingRate == wa2.cacheAgingRate


# End Web Acceleration tests

# Begin Web Security tests


class iTestWebSecurity(object):
    def test_load(self, request, bigip):
        ws1 = bigip.ltm.profile.\
            web_securitys.websecurity.load(name='websecurity')
        assert ws1.name == 'websecurity'


# End Web Security tests

# Begin Xml tests


class TestXml(object):
    def test_MCURDL(self, request, bigip):
        testxml = HelperTest('Xmls')
        testxml.test_MCURDL(request, bigip)


# End Xml tests
