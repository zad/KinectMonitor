function hours = getHours( camera, date )
%GETHOURS Summary of this function goes here
%   Detailed explanation goes here
d = dir(fullfile(getSampleDir(), camera, date));
isDir = [d(:).isdir];
hours = {d(isDir).name}';
hours(ismember(hours,{'.','..'})) = [];
valid = ones(1, length(hours));
for i = 1:length(hours)
    hour = hours(i);
    mins = getMinutes( camera, date, hour{1} );
    if length(mins) > 5
        valid(i) = 0;
    end
end
hours(logical(valid)) = [];

