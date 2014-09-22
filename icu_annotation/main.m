function varargout = main(varargin)
% MAIN MATLAB code for main.fig
%      MAIN, by itself, creates a new MAIN or raises the existing
%      singleton*.
%
%      H = MAIN returns the handle to a new MAIN or the handle to
%      the existing singleton*.
%
%      MAIN('CALLBACK',hObject,eventData,handles,...) calls the local
%      function named CALLBACK in MAIN.M with the given input arguments.
%
%      MAIN('Property','Value',...) creates a new MAIN or raises the
%      existing singleton*.  Starting from the left, property value pairs are
%      applied to the GUI before main_OpeningFcn gets called.  An
%      unrecognized property name or invalid value makes property application
%      stop.  All inputs are passed to main_OpeningFcn via varargin.
%
%      *See GUI Options on GUIDE's Tools menu.  Choose "GUI allows only one
%      instance to run (singleton)".
%
% See also: GUIDE, GUIDATA, GUIHANDLES

% Edit the above text to modify the response to help main

% Last Modified by GUIDE v2.5 16-Sep-2014 15:37:08

% Begin initialization code - DO NOT EDIT
gui_Singleton = 1;
gui_State = struct('gui_Name',       mfilename, ...
                   'gui_Singleton',  gui_Singleton, ...
                   'gui_OpeningFcn', @main_OpeningFcn, ...
                   'gui_OutputFcn',  @main_OutputFcn, ...
                   'gui_LayoutFcn',  [] , ...
                   'gui_Callback',   []);
if nargin && ischar(varargin{1})
    gui_State.gui_Callback = str2func(varargin{1});
end

if nargout
    [varargout{1:nargout}] = gui_mainfcn(gui_State, varargin{:});
else
    gui_mainfcn(gui_State, varargin{:});
end
% End initialization code - DO NOT EDIT


% --- Executes just before main is made visible.
function main_OpeningFcn(hObject, eventdata, handles, varargin)
% This function has no output args, see OutputFcn.
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
% varargin   command line arguments to main (see VARARGIN)

% Choose default command line output for main
handles.output = hObject;

% Update handles structure
guidata(hObject, handles);

% UIWAIT makes main wait for user response (see UIRESUME)
% uiwait(handles.figure1);


% --- Outputs from this function are returned to the command line.
function varargout = main_OutputFcn(hObject, eventdata, handles) 
% varargout  cell array for returning output args (see VARARGOUT);
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Get default command line output from handles structure
varargout{1} = handles.output;


% --- Executes on slider movement.
function slider1_Callback(hObject, eventdata, handles)
% hObject    handle to slider1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'Value') returns position of slider
%        get(hObject,'Min') and get(hObject,'Max') to determine range of slider
global min %play
%if play == 0 % pause
    min = get(hObject, 'Value');
    updateFigure(handles)
%else
%    set(hObject, 'Value', min);
%    mbox('Cannot control slider in play mode', 'Warning');
%end

function playFigure(handles)
global min play_speed hour_id
min = min + play_speed;
if min > 59
    min = min - 59;
    % hour + 1
    hour_id = hour_id + 1;
    % check if hour_id exists
    hours = cellstr(get(handles.popupmenu4,'String'));
    if hour_id <= length(hours)
        set(handles.popupmenu4, 'Value', hour_id);        
    else
        set(handles.togglebutton1, 'Value', 0);
        set(handles.togglebutton1, 'String', 'Play');
        return;
    end
end
% update slider
set(handles.slider1, 'Value', min);
% update figure
updateFigure(handles)

% --- Executes during object creation, after setting all properties.
function slider1_CreateFcn(hObject, eventdata, handles)
% hObject    handle to slider1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: slider controls usually have a light gray background.
if isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor',[.9 .9 .9]);
end

set(hObject, 'max', 59, 'min', 0, 'sliderstep', [1/60, 1/6], 'Value', 0)

function updateSlider(handles)
set(handles.slider1, 'max', 59, 'min', 0, 'sliderstep', [1/60, 1/6], 'Value', 0)
global min
min = 0;
updateFigure(handles);

function updateHourBar(handles, minutes, selected_min)
minutes_bar = zeros(1,60);

for i = 1:length(minutes)
    min_num = str2num(minutes{i});
    minutes_bar(min_num+1) = 1;
end
axes(handles.axes3);
bar(minutes_bar, 'style', 'histc');
hold on
line([selected_min+1, selected_min+1], [0, 1], 'Color', 'r', 'LineWidth', 2)
set(handles.axes3,'YTick',[]);
set(handles.axes3,'XTick',[], 'XLim', [1 61]);
hold off
        

function updateFigure(handles)
global cam_id date_id hour_id min current_time

if cam_id ~= 1 && date_id ~= 1 && hour_id ~= 1
    cameras = cellstr(get(handles.popupmenu6,'String'));
    cam = cameras{cam_id};
    dates = cellstr(get(handles.popupmenu3,'String'));
    date = dates{date_id};
    hours = cellstr(get(handles.popupmenu4,'String'));
    hour = hours{hour_id};
    min_str = int2str(min);
    if min < 10
        min_str = strcat('0', min_str);
    end
    minutes = getNonEmptyMinutes(cam, date, hour);
    updateHourBar(handles, minutes, min)
    image_path = fullfile(getSampleDir(), cam, date, hour, min_str, '*.jpg');
    images = dir(image_path);
    % draw main figure
    axes(handles.axes1);
    if size(images) > 0
        selected_image = fullfile(getSampleDir(), cam, date, hour, min_str, images(1).name)       
        I = eimreadblur(selected_image,0);
        image(I);
        set(handles.axes1,'YTick',[]);
        set(handles.axes1,'XTick',[]);
    else
        I = imread('/home/zad/Documents/MATLAB/annotation/nofigure.jpg');
        image(I);
        set(handles.axes1,'YTick',[]);
        set(handles.axes1,'XTick',[]);
    end
    % draw secondary figures
    sid = cam_id;
    sid = sid + 1;
    if sid > 4
        sid = 2;
    end
    cam = cameras{sid};
    image_path = fullfile(getSampleDir(), cam, date, hour, min_str, '*.jpg');
    images = dir(image_path);
    axes(handles.axes4);
    if size(images) > 0
        selected_image = fullfile(getSampleDir(), cam, date, hour, min_str, images(1).name)       
        I = eimreadblur(selected_image,0);
        image(I);
        set(handles.axes1,'YTick',[]);
        set(handles.axes1,'XTick',[]);
    else
        I = imread('/home/zad/Documents/MATLAB/annotation/nofigure.jpg');
        image(I);
        set(handles.axes1,'YTick',[]);
        set(handles.axes1,'XTick',[]);
    end
    sid = sid + 1;
    if sid > 4
        sid = 2;
    end
    cam = cameras{sid};
    image_path = fullfile(getSampleDir(), cam, date, hour, min_str, '*.jpg');
    images = dir(image_path);
    axes(handles.axes5);
    if size(images) > 0
        selected_image = fullfile(getSampleDir(), cam, date, hour, min_str, images(1).name)       
        I = eimreadblur(selected_image,0);
        image(I);
        set(handles.axes1,'YTick',[]);
        set(handles.axes1,'XTick',[]);
    else
        I = imread('/home/zad/Documents/MATLAB/annotation/nofigure.jpg');
        image(I);
        set(handles.axes1,'YTick',[]);
        set(handles.axes1,'XTick',[]);
    end
    % update datetime text
    fig_name = sprintf('%s: %s %s:%s', cam, date, hour, min_str);
    current_time = sprintf('%s_%s%s00', date, hour, min_str);
    set(handles.text5, 'String', fig_name)
end

function updatePendingTable()
global cam_id date_id hour_id username label_table start_time end_time 
global handles_popupmenu6 handles_uitable2
if cam_id ~= 1 && date_id ~= 1 && hour_id ~= 1 && ~isempty(username)
    data = {};
    idx = 1;
    cameras = cellstr(get(handles_popupmenu6,'String'));
    cam = cameras{cam_id};
    V = values(label_table);
    for i = 1:length(V)
        L = V(i);
        if L{1}.selected == 1
            data{idx,1} = username;
            data{idx,2} = cam;
            if ~isempty(start_time)
                data{idx,3} = start_time;
            end
            if ~isempty(end_time)
                data{idx,4} = end_time;
            end
            data{idx,5} = char(L{1}.id);
            data{idx,6} = char(L{1}.name);
            data{idx,7} = datestr(now)
            idx = idx + 1;
        end
    end
    set(handles_uitable2, 'Data', data);
end

% --- Executes on selection change in popupmenu1.
function popupmenu1_Callback(hObject, eventdata, handles)
% hObject    handle to popupmenu1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: contents = cellstr(get(hObject,'String')) returns popupmenu1 contents as cell array
%        contents{get(hObject,'Value')} returns selected item from popupmenu1


% --- Executes during object creation, after setting all properties.
function popupmenu1_CreateFcn(hObject, eventdata, handles)
% hObject    handle to popupmenu1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: popupmenu controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes on selection change in popupmenu3.
function popupmenu3_Callback(hObject, eventdata, handles)
% hObject    handle to popupmenu3 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: contents = cellstr(get(hObject,'String')) returns popupmenu3 contents as cell array
%        contents{get(hObject,'Value')} returns selected item from popupmenu3
contents = cellstr(get(hObject,'String'));
% date popupmenu
global date_id hour_id
selected = get(hObject,'Value');
if selected == 1
    set(handles.popupmenu4, 'Value', 1);
    hour_id = 1;
else
    if selected ~= date_id
        date = contents{get(hObject,'Value')};
        contents = cellstr(get(handles.popupmenu6,'String'));
        camera = contents{get(handles.popupmenu6, 'Value')};
        hours = getHours(camera, date);
        hours = ['Select Hour' ; hours];
        set(handles.popupmenu4, 'String', hours);
        set(handles.popupmenu4, 'Value', 1);
        hour_id = 1;
    end
end
date_id = selected;

% --- Executes during object creation, after setting all properties.
function popupmenu3_CreateFcn(hObject, eventdata, handles)
% hObject    handle to popupmenu3 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: popupmenu controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes on selection change in popupmenu4.
function popupmenu4_Callback(hObject, eventdata, handles)
% hObject    handle to popupmenu4 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: contents = cellstr(get(hObject,'String')) returns popupmenu4 contents as cell array
%        contents{get(hObject,'Value')} returns selected item from popupmenu4
% hour popupmenu
global hour_id
selected = get(hObject, 'Value');
% update slider and figure
if selected ~= hour_id
    hour_id = selected;
    updateSlider(handles);
end


% --- Executes during object creation, after setting all properties.
function popupmenu4_CreateFcn(hObject, eventdata, handles)
% hObject    handle to popupmenu4 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: popupmenu controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes on selection change in popupmenu5.
function popupmenu5_Callback(hObject, eventdata, handles)
% hObject    handle to popupmenu5 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: contents = cellstr(get(hObject,'String')) returns popupmenu5 contents as cell array
%        contents{get(hObject,'Value')} returns selected item from popupmenu5


% --- Executes during object creation, after setting all properties.
function popupmenu5_CreateFcn(hObject, eventdata, handles)
% hObject    handle to popupmenu5 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: popupmenu controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes on selection change in popupmenu6.
function popupmenu6_Callback(hObject, eventdata, handles)
% hObject    handle to popupmenu6 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: contents = cellstr(get(hObject,'String')) returns popupmenu6 contents as cell array
%        contents{get(hObject,'Value')} returns selected item from popupmenu6

% popupmenu for camera
contents = cellstr(get(hObject,'String'));
selected = get(hObject,'Value');

global cam_id date_id hour_id
if selected == 1 % unselected
    set(handles.popupmenu3, 'Value', 1);
    date_id = 1;
    set(handles.popupmenu4, 'Value', 1);
    hour_id = 1;
else
    if selected ~= cam_id
        camera = contents{selected};
        dates = getDatesByCamera(camera);
        dates = ['Select Date'; dates];
        set(handles.popupmenu3, 'String', dates);
        set(handles.popupmenu3, 'Value', 1);
        date_id = 1;
        set(handles.popupmenu4, 'Value', 1);
        hour_id = 1;
    end
end
cam_id = selected;


% --- Executes during object creation, after setting all properties.
function popupmenu6_CreateFcn(hObject, eventdata, handles)
% hObject    handle to popupmenu6 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: popupmenu controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end
cameras = getCameras();
cameras = ['Select Camera'; cameras];
set(hObject, 'String', cameras); % e.g., {'WICU-room5_1';'WICU-room5_2';'WICU-room5_3'}
global cam_id handles_popupmenu6
cam_id = 1;
handles_popupmenu6 = hObject;

% --- Executes during object creation, after setting all properties.
function axes1_CreateFcn(hObject, eventdata, handles)
% hObject    handle to axes1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: place code in OpeningFcn to populate axes1
% I = imread('~/Downloads/Example.jpg');
% image(I);
% set(hObject,'YTick',[]);
% set(hObject,'XTick',[]);

% --- Executes on selection change in popupmenu7.
function popupmenu7_Callback(hObject, eventdata, handles)
% hObject    handle to popupmenu7 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: contents = cellstr(get(hObject,'String')) returns popupmenu7 contents as cell array
%        contents{get(hObject,'Value')} returns selected item from popupmenu7


% --- Executes during object creation, after setting all properties.
function popupmenu7_CreateFcn(hObject, eventdata, handles)
% hObject    handle to popupmenu7 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: popupmenu controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes on selection change in popupmenu8.
function popupmenu8_Callback(hObject, eventdata, handles)
% hObject    handle to popupmenu8 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: contents = cellstr(get(hObject,'String')) returns popupmenu8 contents as cell array
%        contents{get(hObject,'Value')} returns selected item from popupmenu8


% --- Executes during object creation, after setting all properties.
function popupmenu8_CreateFcn(hObject, eventdata, handles)
% hObject    handle to popupmenu8 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: popupmenu controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes on selection change in listbox1.
function listbox1_Callback(hObject, eventdata, handles)
% hObject    handle to listbox1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: contents = cellstr(get(hObject,'String')) returns listbox1 contents as cell array
%        contents{get(hObject,'Value')} returns selected item from listbox1


% --- Executes during object creation, after setting all properties.
function listbox1_CreateFcn(hObject, eventdata, handles)
% hObject    handle to listbox1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: listbox controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes on button press in pushbutton5.
function pushbutton5_Callback(hObject, eventdata, handles)
% hObject    handle to pushbutton5 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
global start_time current_time
if length(current_time) > 0
    start_time = current_time;
    updatePendingTable()
end

% --- Executes on button press in pushbutton7.
function pushbutton7_Callback(hObject, eventdata, handles)
% hObject    handle to pushbutton7 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
% Save pending annotations to file
global handles_uitable2 start_time end_time
data = get(handles_uitable2, 'Data');
cell2csv('annotation.csv', data);
set(handles_uitable2, 'Data', {});
start_time = '';
end_time = '';

% --- Executes on button press in pushbutton8.
function pushbutton8_Callback(hObject, eventdata, handles)
% hObject    handle to pushbutton8 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
global start_time current_time end_time
if length(current_time) > 0
    end_time = current_time;
    updatePendingTable()
end


function edit1_Callback(hObject, eventdata, handles)
% hObject    handle to edit1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edit1 as text
%        str2double(get(hObject,'String')) returns contents of edit1 as a double
global username
username = get(hObject, 'String');

% --- Executes during object creation, after setting all properties.
function edit1_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edit1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end
global username
username = '';
set(hObject, 'String', username);




% --- Executes during object creation, after setting all properties.
function uipanel5_CreateFcn(hObject, eventdata, handles)
% hObject    handle to uipanel5 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called
% load check icons
import javax.swing.*
import javax.swing.tree.*;

global iconWidth javaImage_checked javaImage_unchecked global_handles
global_handles = handles;
[I,map] = checkedIcon;
javaImage_checked = im2java(I,map);
[I,map] = uncheckedIcon;
javaImage_unchecked = im2java(I,map);

% javaImage_checked/unchecked are assumed to have the same width
iconWidth = javaImage_unchecked.getWidth;

% create label hash table
global label_table
label_table = containers.Map;

% create top node
root = uitreenode('v0', 'Protocols', 'Protocols', [], false);
protocol_dir = dir('/home/zad/Documents/MATLAB/annotation/protocols/*.xml');
for protocol_xml = {protocol_dir.name}
    protocol_node = uitreenode('v0', protocol_xml, protocol_xml, [], 0);
    % load labels in each protocol
    xmlpath = strcat('/home/zad/Documents/MATLAB/annotation/protocols/', protocol_xml);
    xmlpath = xmlpath{1};
    tree = xmlread(xmlpath);
    labels = tree.getChildNodes.getElementsByTagName('labels');
    labellist = labels.item(0).getChildNodes.getElementsByTagName('label');
    for count = 1:labellist.getLength
        label = labellist.item(count-1);
        L(count).name = label.getElementsByTagName('name').item(0).getTextContent;
        L(count).id = label.getElementsByTagName('id').item(0).getTextContent;
        L(count).selected = 0;
        label_table(char(L(count).name)) = L(count);
        labelnode = uitreenode('v0', 'unselected', L(count).name, [], 1);
        labelnode.setIcon(javaImage_unchecked);
        protocol_node.add(labelnode);
    end
    
    root.add(protocol_node)
end




[tree, container] = uitree('v0', 'Root', root);

set(container, 'Parent',hObject);
set(container, 'Units','normalized', 'Position',[0 0 1 1]);

% set treeModel
treeModel = DefaultTreeModel(root);
tree.setModel(treeModel);
% we often rely on the underlying java tree
jtree = handle(tree.getTree,'CallbackProperties');
set(tree, 'NodeSelectedCallback', @selected_cb );
% make root the initially selected node
tree.setSelectedNode( root );

% MousePressedCallback is not supported by the uitree, but by jtree
set(jtree, 'MousePressedCallback', @mousePressedCallback);

% Set the mouse-press callback
function mousePressedCallback(jtree, eventData) %,additionalVar)
% if eventData.isMetaDown % right-click is like a Meta-button
% if eventData.getClickCount==2 % how to detect double clicks
global iconWidth javaImage_checked javaImage_unchecked username
global current_time
if isempty(username)
    msgbox('Please input your name first','Warning');
    return;
end
if isempty(current_time)
    msgbox('Please select camera, date, and hour', 'Warning');
    return;
end

% Get the clicked node
clickX = eventData.getX;
clickY = eventData.getY;
treePath = jtree.getPathForLocation(clickX, clickY);
% check if a node was clicked
global label_table
if ~isempty(treePath)
  % check if the checkbox was clicked
  if clickX <= (jtree.getPathBounds(treePath).x+iconWidth)
    node = treePath.getLastPathComponent;
    nodeValue = node.getValue;
    nodeName = node.getName;
    % as the value field is the selected/unselected flag,
    % we can also use it to only act on nodes with these values
    switch nodeValue
      case 'selected'
        node.setValue('unselected');
        label = label_table(char(nodeName));
        label.selected = 0;
        label_table(char(nodeName)) = label;
        node.setIcon(javaImage_unchecked);
        jtree.treeDidChange();
        updatePendingTable();
      case 'unselected'
        node.setValue('selected');
        label = label_table(char(nodeName));
        label.selected = 1;
        node.setIcon(javaImage_checked);
        label_table(char(nodeName)) = label;
        jtree.treeDidChange();
        updatePendingTable();
    end
  end
end

 
function selected_cb( tree, ev )
nodes = tree.getSelectedNodes;
node = nodes(1);
path = node2path(node);

function path = node2path(node)
path = node.getPath;
for i=1:length(path);
  p{i} = char(path(i).getName);
end
if length(p) > 1
  path = fullfile(p{:});
else
  path = p{1};
end
  

function [I,map] = checkedIcon()
I = uint8(...
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0;
     2,2,2,2,2,2,2,2,2,2,2,2,2,0,0,1;
     2,2,2,2,2,2,2,2,2,2,2,2,0,2,3,1;
     2,2,1,1,1,1,1,1,1,1,1,0,2,2,3,1;
     2,2,1,1,1,1,1,1,1,1,0,1,2,2,3,1;
     2,2,1,1,1,1,1,1,1,0,1,1,2,2,3,1;
     2,2,1,1,1,1,1,1,0,0,1,1,2,2,3,1;
     2,2,1,0,0,1,1,0,0,1,1,1,2,2,3,1;
     2,2,1,1,0,0,0,0,1,1,1,1,2,2,3,1;
     2,2,1,1,0,0,0,0,1,1,1,1,2,2,3,1;
     2,2,1,1,1,0,0,1,1,1,1,1,2,2,3,1;
     2,2,1,1,1,0,1,1,1,1,1,1,2,2,3,1;
     2,2,1,1,1,1,1,1,1,1,1,1,2,2,3,1;
     2,2,2,2,2,2,2,2,2,2,2,2,2,2,3,1;
     2,2,2,2,2,2,2,2,2,2,2,2,2,2,3,1;
     1,3,3,3,3,3,3,3,3,3,3,3,3,3,3,1]);
 map = [0.023529,0.4902,0;
        1,1,1;
        0,0,0;
        0.50196,0.50196,0.50196;
        0.50196,0.50196,0.50196;
        0,0,0;
        0,0,0;
        0,0,0];
 
  function [I,map] = uncheckedIcon()
 I = uint8(...
   [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1;
    2,2,2,2,2,2,2,2,2,2,2,2,2,2,1,1;
    2,2,2,2,2,2,2,2,2,2,2,2,2,2,3,1;
    2,2,1,1,1,1,1,1,1,1,1,1,2,2,3,1;
    2,2,1,1,1,1,1,1,1,1,1,1,2,2,3,1;
    2,2,1,1,1,1,1,1,1,1,1,1,2,2,3,1;
    2,2,1,1,1,1,1,1,1,1,1,1,2,2,3,1;
    2,2,1,1,1,1,1,1,1,1,1,1,2,2,3,1;
    2,2,1,1,1,1,1,1,1,1,1,1,2,2,3,1;
    2,2,1,1,1,1,1,1,1,1,1,1,2,2,3,1;
    2,2,1,1,1,1,1,1,1,1,1,1,2,2,3,1;
    2,2,1,1,1,1,1,1,1,1,1,1,2,2,3,1;
    2,2,1,1,1,1,1,1,1,1,1,1,2,2,3,1;
    2,2,2,2,2,2,2,2,2,2,2,2,2,2,3,1;
    2,2,2,2,2,2,2,2,2,2,2,2,2,2,3,1;
    1,3,3,3,3,3,3,3,3,3,3,3,3,3,3,1]);
 map = ...
  [0.023529,0.4902,0;
   1,1,1;
   0,0,0;
   0.50196,0.50196,0.50196;
   0.50196,0.50196,0.50196;
   0,0,0;
   0,0,0;
   0,0,0];


% --- Executes on button press in pushbutton9.
function pushbutton9_Callback(hObject, eventdata, handles)
% hObject    handle to pushbutton9 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
set(handles.uitable2, 'Data', {});
global start_time end_time
start_time = '';
end_time = '';

% --- Executes during object creation, after setting all properties.
function uitable2_CreateFcn(hObject, eventdata, handles)
% hObject    handle to uitable2 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called
global handles_uitable2 start_time end_time
handles_uitable2 = hObject;
start_time = '';
end_time = '';


% --- Executes on selection change in popupmenu9.
function popupmenu9_Callback(hObject, eventdata, handles)
% hObject    handle to popupmenu9 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: contents = cellstr(get(hObject,'String')) returns popupmenu9 contents as cell array
%        contents{get(hObject,'Value')} returns selected item from popupmenu9
selected = get(hObject,'Value');
global play_speed
switch selected
    case 1
        play_speed = 1
    case 2
        play_speed = 2
    case 3
        play_speed = 3
end

% --- Executes during object creation, after setting all properties.
function popupmenu9_CreateFcn(hObject, eventdata, handles)
% hObject    handle to popupmenu9 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: popupmenu controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end
global play_speed
play_speed = 1;

% --- Executes on button press in togglebutton1.
function togglebutton1_Callback(hObject, eventdata, handles)
% hObject    handle to togglebutton1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: get(hObject,'Value') returns toggle state of togglebutton1
global cam_id date_id hour_id min current_time play

if cam_id ~= 1 && date_id ~= 1 && hour_id ~= 1
    if get(hObject, 'Value')
        set(hObject, 'String', 'Pause');
    else
        set(hObject, 'String', 'Play');
    end
    while get(hObject, 'Value');
        pause(0.1)
        playFigure(handles);
    end
else
    set(hObject, 'Value', 0);
    set(hObject, 'String', 'Play');
    msgbox('Please select camera, date, and hour', 'Warning');
end


% --- Executes during object creation, after setting all properties.
function text5_CreateFcn(hObject, eventdata, handles)
% hObject    handle to text5 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called


% --- Executes during object creation, after setting all properties.
function uipanel3_CreateFcn(hObject, eventdata, handles)
% hObject    handle to uipanel3 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called
global cam_id date_id hour_id min current_time play 
cam_id = 1;
date_id = 1;
hour_id = 1;
min = 0;
current_time = '';
play = 0;
