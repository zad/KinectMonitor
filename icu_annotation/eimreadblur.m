function im = eimreadblur(filename,i)

filtersize = 20
if nargin < 2
    i = [];
end

if system(['python decrypt.py ' filename ' tmp' num2str(i) '.jpg' ]) == 0
    im = imread(['tmp' num2str(i) '.jpg']);
    delete(['tmp' num2str(i) '.jpg']);
    
    filenamedepth = strrep(filename, 'color', 'depth');
    filenamedepth = strrep(filenamedepth, 'image', 'depth');
    filenamedepth = strrep(filenamedepth, 'jpg', 'png');
    
    try
        imdepth = imread(filenamedepth);
    catch
        imdepth = [];
    end
    
    if ~isempty(imdepth)
        depsort = sort(imdepth(:));
        dep1 = depsort(round(length(imdepth(:))/3));
        dep2 = depsort(round(length(imdepth(:))/3*2));
        
        %             im = 255 - im;
        fsize0 = filtersize;
        h0 = fspecial('average', fsize0);
        fsize1 = filtersize/2;
        h1 = fspecial('average', fsize1);
        fsize2 = filtersize/4;
        h2 = fspecial('average', fsize2);
        parfor j = 1:3
            imf0 = imfilter(adapthisteq(im(:,:,j)), h0);
            imf1 = imfilter(adapthisteq(im(:,:,j)), h1);
            imf2 = imfilter(adapthisteq(im(:,:,j)), h2);
            imftmp = imf0;
            imftmp(imdepth>dep1) = imf1(imdepth>dep1);
            imftmp(imdepth>dep2) = imf2(imdepth>dep2);
            imf(:,:,j) = imftmp;
        end
    else
        h = fspecial('average', filtersize);
        parfor j = 1:3
            imf(:,:,j) = imfilter(adapthisteq(im(:,:,j)), h);
        end
    end
    
    im = imf;
else
    im = [];
end

end