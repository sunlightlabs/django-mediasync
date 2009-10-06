
def compress(data, level=6):
    zbuf = cStringIO.StringIO()
    zfile = gzip.GzipFile(mode='wb', compresslevel=level, fileobj=zbuf)
    zfile.write(data)
    zfile.close()
    gzdata = zbuf.getvalue()
    zbuf.close()
    return gzdata