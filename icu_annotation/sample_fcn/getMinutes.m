function minutes = getMinutes( camera, date, hour )
%GETHOURS Summary of this function goes here
%   Detailed explanation goes here
d = dir(fullfile(getSampleDir(), camera, date, hour));
isDir = [d(:).isdir];
minutes = {d(isDir).name}';
minutes(ismember(minutes,{'.','..'})) = [];

end

