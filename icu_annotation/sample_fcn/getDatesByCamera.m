function dates = getDatesByCamera( camera )
%GETDATESBYCAMERA Summary of this function goes here
%   Detailed explanation goes here
d = dir(fullfile(getSampleDir(), camera));
isDir = [d(:).isdir];
dates = {d(isDir).name}';
dates(ismember(dates,{'.','..'})) = [];
valid = ones(1, length(dates));
for i = 1:length(dates)
    date = dates(i);
    hours = getHours( camera, date{1} );
    if ~isempty(hours)
        valid(i) = 0;
    end
end
dates(logical(valid)) = [];
end

