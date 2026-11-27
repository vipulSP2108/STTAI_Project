"""Save the built image as gzip, verify its archive, and record checksums."""
import gzip,hashlib,json,pathlib,shutil,subprocess,tarfile,time
out=pathlib.Path(__file__).resolve().parent
tag='voice-helpdesk-asr:indic-v2'
info=json.loads(subprocess.check_output(['docker','image','inspect',tag]))[0]
archive=out/'docker_image.tar.gz'
if archive.exists():raise SystemExit('Archive already exists; refusing to overwrite it')
partial=out/'docker_image.tar.gz.partial'
print('Saving image:',info['Id'],flush=True)
start=time.time()
with (out/'docker_save_stderr.log').open('wb') as err, partial.open('wb') as dest:
 proc=subprocess.Popen(['docker','save',tag],stdout=subprocess.PIPE,stderr=err)
 try:
  with gzip.GzipFile(filename='',mode='wb',fileobj=dest,mtime=0,compresslevel=6) as zipped:
   shutil.copyfileobj(proc.stdout,zipped,1024*1024)
 finally:proc.stdout.close()
 code=proc.wait()
if code:raise SystemExit(f'docker save failed: {code}; see docker_save_stderr.log')
print('Compressed archive written; checking gzip CRC and tar contents',flush=True)
# Read the complete gzip stream through EOF, validating its CRC/trailer.
with gzip.open(partial,'rb') as stream:
 while stream.read(1024*1024):pass
with tarfile.open(partial,'r:gz') as tar:
 names=tar.getnames()
 if 'manifest.json' not in names:raise RuntimeError('Docker archive manifest missing')
 manifest=json.load(tar.extractfile('manifest.json'))
 if not any(tag in (entry.get('RepoTags') or []) for entry in manifest):raise RuntimeError('Expected image tag missing')
partial.replace(archive)
hash_value=hashlib.file_digest(archive.open('rb'),'sha256').hexdigest()
(out/'docker_image.tar.gz.sha256').write_text(hash_value+'  docker_image.tar.gz\n',encoding='ascii')
metadata={'tag':tag,'image_id':info['Id'],'os':info['Os'],'architecture':info['Architecture'],'archive':archive.name,'archive_bytes':archive.stat().st_size,'archive_sha256':hash_value,'git_commit':info['Config']['Env'],'gzip_crc_verified':True,'docker_manifest_verified':True,'packaging_seconds':round(time.time()-start,2)}
# Include provenance fields only, excluding all unrelated environment entries.
metadata['git_commit']=next((s.split('=',1)[1] for s in metadata['git_commit'] if s.startswith('GIT_COMMIT=')),None)
(out/'archive_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
print(json.dumps(metadata,indent=2),flush=True)
