function minutes = getNonEmptyMinutes( camera, date, hour )
%GETHOURS Summary of this function goes here
%   Detailed explanation goes here
d = dir(fullfile(getSampleDir(), camera, date, hour));
isDir = [d(:).isdir];
minutes = {d(isDir).name}';
minutes(ismember(minutes,{'.','..'})) = [];
valid = ones(1, length(minutes));
for i = 1:length(minutes)
    min = minutes(i);
    d = dir(fullfile(getSampleDir(), camera, date, hour, min{1} ));
    
    secs = {d.name}';
    
    if length(secs) > 2
        valid(i) = 0;
    end
end
minutes(logical(valid)) = [];
end

