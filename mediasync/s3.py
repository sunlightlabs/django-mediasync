import cStringIO
import datetime
import gzip

def compress(s):
    zbuf = cStringIO.StringIO()
    zfile = gzip.GzipFile(mode='wb', compresslevel=6, fileobj=zbuf)
    zfile.write(s)
    zfile.close()
    return zbuf.getvalue()

class S3(object):
    
    def __init__(key, secret):
        self._key = key
        self._secret = secret

    def upload(path, content, content_type):
    
        now = datetime.datetime.utcnow()
        rfc_now = now.strftime("%a, %d %b %Y %X GMT")
        expires = now + datetime.timedelta(1)

        content = compress(content)
        checksum = base64.b64encode(md5.new(content).digest())

        to_sign = "\n".join(["PUT", checksum, content_type, rfc_now, "x-amz-acl:public-read", "/%s%s" % (AWS_BUCKET, AWS_PATH)])
        sig = base64.encodestring(hmac.new(AWS_SECRET, to_sign, sha).digest()).strip()

        headers = {
            "x-amz-acl": "public-read",
            "Expires": expires.strftime("%a, %d %b %Y %H:%M:%S UTC"),
            "Content-Type": content_type,
            "Content-Length": len(content),
            "Content-MD5": checksum,
            "Content-Encoding": "gzip",
            "Date": rfc_now,
            "Authorization": "AWS %s:%s" % (AWS_KEY, sig)
        }

        s3_conn = httplib.HTTPConnection(AWS_BUCKET)
        s3_conn.request("PUT", AWS_PATH, content, headers)
        response = s3_conn.getresponse()
        s3_conn.close()