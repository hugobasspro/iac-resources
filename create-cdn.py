from huaweicloudsdkcore.auth.credentials import GlobalCredentials
from huaweicloudsdkcdn.v1.cdn_client import CdnClient
from huaweicloudsdkcdn.v1.region.cdn_region import CdnRegion
from huaweicloudsdkcdn.v1.model import *
from huaweicloudsdkscm.v3.region.scm_region import ScmRegion
from huaweicloudsdkscm.v3 import *
import sys

def find_ssl_certificate(scm_client, certificate_name) -> str:
    """
    Find an SSL certificate by its name.

    Parameters:
    scm_client (ScmClient): The SCM client instance.
    certificate_name (str): The name of the SSL certificate to find.

    Returns:
    str: The ID of the SSL certificate if found, an empty string otherwise.
    """
    try:
        request = ListCertificatesRequest()
        response = scm_client.list_certificates(request)
        for certificate in response.certificates:
            if certificate.name == certificate_name:
                return certificate.id
        return ""
    except Exception as e:
        print(f"Exception occurred while searching for SSL certificate '{certificate_name}': {e}")
        return ""

def create_cdn_domain(scm_client, cdn_client, domain_name, subdomain, region, bucket_name, ssl_certificate_name) -> bool:
    """
    Create a new CDN domain.

    Parameters:
    scm_client (ScmCLient): the certificate client instance.
    cdn_client (CdnClient): The CDN client instance.
    domain_name (str): The name of the CDN domain to create.
    region (str): The region where to deploy.
    subdomain (str): The name of the subdomain to create.
    bucket_name (str): The name of the bucket to use as the origin.
    ssl_certificate_name (str): The name of the SSL certificate to use.

    Returns:
    bool: True if the CDN domain was created successfully, False otherwise.
    """
    try:
        request = PushCertificateRequest()
        ssl_certificate_id = find_ssl_certificate(scm_client, ssl_certificate_name)
        print (ssl_certificate_id)
        request.certificate_id = ssl_certificate_id
        request.body = PushCertificateRequestBody(
            target_service="CDN",
            target_project=region
        )
        response = scm_client.push_certificate(request)
        print(response)
    except Exception as e:
        print(f"Exception occurred while pushing certificate '{ssl_certificate_name}': {e}")
        if (e.error_code != 'SCM.0211'):
            return False

    try:
        sources = [Sources(ip_or_domain=f'{bucket_name}.obs-website.{region}.myhuaweicloud.com', origin_type='obs_bucket', active_standby=1, enable_obs_web_hosting=1)]
        domain_body = DomainBody(domain_name=domain_name, business_type='web', sources=sources, service_area='outside_mainland_china' )
        request = CreateDomainRequest()
        request.body = CreateDomainRequestBody(domain=domain_body)
        response = cdn_client.create_domain(request)
        if response.domain.id:
            print(f"CDN domain '{domain_name}' created successfully with ID: {response.domain.id}")

            request = UpdateHttpsInfoRequest()
            request.domain_id = response.domain.id
            httpsbody = HttpInfoRequestBody(
                cert_name=ssl_certificate_name,
                https_status=2,
                certificate_type=1
            )
            request.body = HttpInfoRequest(
                https=httpsbody
            )
            response1 = cdn_client.update_https_info(request)
            print(response1)

            request = UpdateDomainFullConfigRequest()
            request.domain_name = domain_name
            listOriginRequestUrlRewriteConfigs = [
                OriginRequestUrlRewrite(
                    priority=1,
                    match_type="wildcard",
                    source_url="/*",
                    target_url=f"/{subdomain}/$1"
                )
            ]
            configsbody = Configs(
                origin_request_url_rewrite=listOriginRequestUrlRewriteConfigs
            )
            request.body = ModifyDomainConfigRequestBody(
                configs=configsbody
            )
            response1 = cdn_client.update_domain_full_config(request)
            print(response1)

            request = UpdateResponseHeaderRequest()
            request.domain_id = response.domain.id
            headersbody = HeaderMap(
                content_disposition="inline"
            )
            request.body = HeaderBody(
                headers=headersbody
            )
            response1 = cdn_client.update_response_header(request)
            print(response1)

            return True
        else:
            print(f"Error: Unable to create CDN domain '{domain_name}'.")
            return False
    except Exception as e:
        print(f"Exception occurred while creating CDN domain '{domain_name}': {e}")
        return False

def main(domain_name, subdomain, ak, sk, region, bucket_name, ssl_certificate_name) -> bool:
    """
    Main function to create a new CDN domain.

    Parameters:
    domain_name (str): The name of the CDN domain to create.
    subdomain (str): The name of the subdomain to create.
    ak (str): The access key ID for the Huawei Cloud account.
    sk (str): The secret access key for the Huawei Cloud account.
    region (str): The region where to deploy
    bucket_name (str): The name of the bucket to use as the origin.
    ssl_certificate_name (str): The name of the SSL certificate to use.

    Returns:
    bool: True if the CDN domain was created successfully, False otherwise.
    """
    credentials = GlobalCredentials(ak, sk)
    scm_client = ScmClient.new_builder() \
        .with_credentials(credentials) \
        .with_region(ScmRegion.value_of("ap-southeast-1")) \
        .build()

    cdn_client = CdnClient.new_builder() \
        .with_credentials(credentials) \
        .with_region(CdnRegion.value_of("ap-southeast-1")) \
        .build()

    return create_cdn_domain(scm_client, cdn_client, domain_name, subdomain, region, bucket_name, ssl_certificate_name)

if __name__ == "__main__":
    if len(sys.argv) != 8:
        print("Usage: python create_cdn_domain.py <domain_name> <subdomain> <access_key_id> <secret_access_key> <region> <bucket_name> <ssl_certificate_name>")
        sys.exit(1)

    domain_name, subdomain, ak, sk, region, bucket_name, ssl_certificate_name = sys.argv[1:]

    if main(domain_name, subdomain, ak, sk, region, bucket_name, ssl_certificate_name):
        print(f"CDN domain '{domain_name}' created successfully.")
    else:
        print(f"Failed to create CDN domain '{domain_name}'.")