function cameras = getCameras()
d = dir(getSampleDir());
isDir = [d(:).isdir];
cameras = {d(isDir).name}';
cameras(ismember(cameras,{'.','..'})) = [];
end
