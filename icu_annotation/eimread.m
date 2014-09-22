function im = eimread(filename,i)

if nargin < 2
    i = [];
end

if system(['python decrypt.py ' filename ' tmp' num2str(i) '.jpg' ]) == 0
    im = imread(['tmp' num2str(i) '.jpg']);
    delete(['tmp' num2str(i) '.jpg']);
else
    im = [];
end

end