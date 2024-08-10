classdef ASL_ProjectCode < matlab.apps.AppBase

    % Properties that correspond to app components
    properties (Access = public)
        UIFigure                       matlab.ui.Figure
        TabGroup                       matlab.ui.container.TabGroup
        HomeTab                        matlab.ui.container.Tab
        PleaseWaitLabel                matlab.ui.control.Label
        MaskButton                     matlab.ui.control.Button
        MoreDisplayOptionsButton       matlab.ui.control.Button
        YourdirectoryEditField         matlab.ui.control.EditField
        YourdirectoryEditFieldLabel    matlab.ui.control.Label
        WelcomePleaseselectyourdirectoryLabel  matlab.ui.control.Label
        SelectDirectoryButton          matlab.ui.control.Button
        PREPARATIONCOMPLETELabel       matlab.ui.control.Label
        ErrorLabel                     matlab.ui.control.Label
        PrepareButton                  matlab.ui.control.Button
        CBFDisplayButton               matlab.ui.control.Button
        StartAgainButton               matlab.ui.control.Button
        Image                          matlab.ui.control.Image
        Axes2                          matlab.ui.control.UIAxes
        Axes1                          matlab.ui.control.UIAxes
        DisplayOptionsTab              matlab.ui.container.Tab
        CLEARButton                    matlab.ui.control.Button
        ReturnHomeButton               matlab.ui.control.Button
        ConfirmandDisplayButton        matlab.ui.control.Button
        NumberofRowstoDisplayDropDown  matlab.ui.control.DropDown
        SelectNumberofRowstoDisplayLabel  matlab.ui.control.Label
        UIAxes_3row_6                  matlab.ui.control.UIAxes
        UIAxes_3row_5                  matlab.ui.control.UIAxes
        UIAxes_3row_4                  matlab.ui.control.UIAxes
        UIAxes_3row_3                  matlab.ui.control.UIAxes
        UIAxes_3row_2                  matlab.ui.control.UIAxes
        UIAxes_3row_1                  matlab.ui.control.UIAxes
        UIAxes_2row_4                  matlab.ui.control.UIAxes
        UIAxes_2row_3                  matlab.ui.control.UIAxes
        UIAxes_2row_2                  matlab.ui.control.UIAxes
        UIAxes_2row_1                  matlab.ui.control.UIAxes
        UIAxes_1row_2                  matlab.ui.control.UIAxes
        UIAxes_1row                    matlab.ui.control.UIAxes
        MaskTab                        matlab.ui.container.Tab
        Label_2                        matlab.ui.control.Label
        instructionLabel2              matlab.ui.control.Label
        RestartButton                  matlab.ui.control.Button
        returnHomeButton2              matlab.ui.control.Button
        MASKINGCOMPLETELabel           matlab.ui.control.Label
        instructionLabel               matlab.ui.control.Label
        STARTButton                    matlab.ui.control.Button
        displayMASK                    matlab.ui.control.UIAxes
        maskImage                      matlab.ui.control.UIAxes
        originalImage                  matlab.ui.control.UIAxes
    end

    
    properties (Access = private)
        % Tracks mask iterations
        maskNumberStart = 1;
        maskNumberSave = 1; 

        % 0: No mask file saved or exists
        % 1: Mask file exists
        maskCBF = 0;
        
    end
    
    methods (Access = private)
        
        % Clears the axes on Display Options screen
        function clearOptionsAxes(app)
            cla(app.UIAxes_1row);
            colorbar(app.UIAxes_1row,  "off");
            
            cla(app.UIAxes_1row_2);
            colorbar(app.UIAxes_1row_2,  "off");
            
            % 2 row clear
            cla(app.UIAxes_2row_1);
            colorbar(app.UIAxes_2row_1,  "off");

            cla(app.UIAxes_2row_2);
            colorbar(app.UIAxes_2row_2,  "off");

            cla(app.UIAxes_2row_3);
            colorbar(app.UIAxes_2row_3,  "off");

            cla(app.UIAxes_2row_4);
            colorbar(app.UIAxes_2row_4,  "off");

            % 3 row clear
            cla(app.UIAxes_3row_1);
            colorbar(app.UIAxes_3row_1,  "off");
            
            cla(app.UIAxes_3row_2);
            colorbar(app.UIAxes_3row_2,  "off");
            
            cla(app.UIAxes_3row_3);
            colorbar(app.UIAxes_3row_3,  "off");

            cla(app.UIAxes_3row_4);
            colorbar(app.UIAxes_3row_4,  "off");

            cla(app.UIAxes_3row_5);
            colorbar(app.UIAxes_3row_5,  "off");

            cla(app.UIAxes_3row_6);
            colorbar(app.UIAxes_3row_6,  "off");

            % After rows are cleared, update button visibility
            app.CLEARButton.Visible = 'off';
            app.ConfirmandDisplayButton.Visible = 'on';
            
        end

        function clearMaskTab(app)
            % Clears the "Mask" tab
            app.STARTButton.Visible = 'on';
          
            cla(app.displayMASK);
            colorbar(app.displayMASK, 'off');
          
            app.maskImage.Title.Visible = 'on';
            app.originalImage.Title.Visible = 'on';

            app.RestartButton.Visible = 'off';
            app.MASKINGCOMPLETELabel.Visible = 'off';

            app.maskImage.Visible = 'on';
            app.originalImage.Visible = 'on';

            app.maskNumberStart = 1;

            app.maskCBF = 0;
        end
    end


    % Callbacks that handle component events
    methods (Access = private)

        % Button pushed function: SelectDirectoryButton
        function SelectDirectoryButtonPushed(app, event)
            try
             % Opens dialogue box
             select_path = uigetdir;
    
             % Lets user select directory
             app.YourdirectoryEditField.Value = select_path;
             figure(app.UIFigure);
    
             if isfile(strcat(app.YourdirectoryEditField.Value, '/ASL.mat'))
                 a = msgbox("Preparation has already been completed. You can skip the 'Prepare' step.");
                 
                 app.MaskButton.Visible = 'on';
                 app.CBFDisplayButton.Visible = 'on';
                 app.PrepareButton.Visible = 'on';
                 app.MoreDisplayOptionsButton.Visible = 'on';
                 app.StartAgainButton.Visible = 'on';
                 pause(2)
                 try
                     close(a);
                 end
                 figure(app.UIFigure);
             else
                 app.MaskButton.Visible = 'on';
                 app.CBFDisplayButton.Visible = 'on';
                 app.PrepareButton.Visible = 'on';
                 
             end
    
            catch
                b = msgbox("Please try again");
                pause(2)
                try
                    close(b);
                end
                figure(app.UIFigure);
    
            end
        end

        % Button pushed function: PrepareButton
        function PrepareButtonPushed(app, event)

            app.PleaseWaitLabel.Visible = 'on';
    
            try
                [diffmap, dyncheck, dyncheck2] = ASL_Preparation(app.YourdirectoryEditField.Value);
                app.PleaseWaitLabel.Visible = 'off';
                app.PREPARATIONCOMPLETELabel.Visible = 'on';
                
                % Plots both graphs in one axes.
                cla(app.Axes1, 'reset');
                axis(app.Axes1, 'on');
                plot(app.Axes1, dyncheck, '-x', 'LineWidth', 1.5);
                hold(app.Axes1, 'on');
                plot(app.Axes1, dyncheck2, '-o', 'LineWidth', 1.5);
                hold(app.Axes1, 'off');
    
                % Display image
                cla(app.Axes2);
                axes(app.Axes2);
                axis(app.Axes2, 'image');
                imagesc(app.Axes2, diffmap(:, :), [0 6]);
                colormap(app.Axes2, jet);
                colorbar(app.Axes2, 'location', 'Eastoutside', 'FontSize', 18);
                axis(app.Axes2, 'off');

                app.MoreDisplayOptionsButton.Visible = 'on';
          
            catch
                % Updates UI for error screen
                app.CBFDisplayButton.Visible = 'off';
                app.ErrorLabel.Visible = 'on';
                app.PREPARATIONCOMPLETELabel.Visible = 'off';         
                app.StartAgainButton.Visible = 'on';
                app.PleaseWaitLabel.Visible = 'off';
    
            end          
        
        end

        % Button pushed function: CBFDisplayButton
        function CBFDisplayButtonPushed(app, event)
            % After successful preparation, will run the created ASL.mat file
            % to display CBF images
            try 
                % UI
                cla(app.Axes1)
              
                % Paths
                path = app.YourdirectoryEditField.Value;
            
                nslicePath = [path, filesep, 'ASL.mat'];
                load(nslicePath, 'diffmap')
                Nslice = size(diffmap, 3);
            
                maskPath = [path, filesep, 'MASK.mat'];
                   
                     if app.maskCBF == 1
                         maskStatus = 1;
            
                     elseif isfile(maskPath)
                         maskStatus = 1;
            
                     elseif app.maskCBF == 0 
                         maskStatus = 0;
                 
                     end
               
                [PDimg, CBFimg] = ASL_CBF(path, maskStatus, 1:Nslice);
            
                % Display images
                displayImages(app.Axes1, PDimg, 'gray', '');
                
                CBFimage_display(app.Axes2, CBFimg*1.5, [0 400], 'jet', '');
            
                % Makes button visible   
                app.MaskButton.Visible = 'on';
                app.StartAgainButton.Visible = 'on';
                app.MoreDisplayOptionsButton.Visible = 'on';
            catch
                msgbox("Error: Please make sure you have completed the Prepare step")
            end

        end

        % Button pushed function: StartAgainButton
        function StartAgainButtonPushed(app, event)
            % Resets entire UI for new use
            app.StartAgainButton.Visible = 'off';
            app.ErrorLabel.Visible = 'off';
            app.MoreDisplayOptionsButton.Visible = 'off';
            app.MaskButton.Visible = 'off';
            app.CBFDisplayButton.Visible = 'off';
            app.PrepareButton.Visible = 'off';

            % Clears UI
            cla(app.Axes1);
            cla(app.Axes2);
            colorbar(app.Axes2,  "off");
            colorbar(app.Axes1,  "off");
            
            % Changes button and text area visibility to the initial
            app.CBFDisplayButton.Visible = 'off';
            app.YourdirectoryEditField.Value = '';
            app.PREPARATIONCOMPLETELabel.Visible = 'off';
           
            clearOptionsAxes(app);
            clearMaskTab(app);
            app.NumberofRowstoDisplayDropDown.Value = '1 Row';

        end

        % Value changed function: YourdirectoryEditField
        function YourdirectoryEditFieldValueChanged(app, event)
            value = app.YourdirectoryEditField.Value;
            
        end

        % Button pushed function: MoreDisplayOptionsButton
        function MoreDisplayOptionsButtonPushed(app, event)
            % Change tabs
            app.TabGroup.SelectedTab = app.DisplayOptionsTab;

        end

        % Button pushed function: ReturnHomeButton
        function ReturnHomeButtonPushed(app, event)
           % Change tabs
            app.TabGroup.SelectedTab = app.HomeTab;

        end

        % Button pushed function: ConfirmandDisplayButton
        function ConfirmandDisplayButtonPushed(app, event)
            % Displays images according to dropdown menu selection
        
            path = app.YourdirectoryEditField.Value;
            maskPath = [path, filesep, 'MASK.mat'];
        
            if app.maskCBF == 1
                maskStatus = 1;
        
            elseif isfile(maskPath)
                maskStatus = 1;
        
            elseif app.maskCBF == 0 
                maskStatus = 0;

            end
        
            % Loading ASL file for Nslice
            nslicePath = [path, filesep, 'ASL.mat'];
            load(nslicePath, 'diffmap')
            Nslice = size(diffmap, 3);
        
            switch app.NumberofRowstoDisplayDropDown.Value
                
                case '1 Row'              
                    % GRAPHING
                    [PDimg, CBFimg] = ASL_CBF(path, maskStatus, 1:Nslice);
        
                    displayImages(app.UIAxes_1row, PDimg, 'gray', '');
                    CBFimage_display(app.UIAxes_1row_2, CBFimg*1.5, [0 400], 'jet', '');
        
               %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        
                case '2 Rows'
                    % Total number of rows
                    totalRows = 2;
        
                    if mod(Nslice, totalRows) == 0
                        firstRow  = Nslice/totalRows;
                    else
                        firstRow = mod(Nslice, totalRows) + floor(Nslice/totalRows);  
                    end
                    
                    % GRAPHING   
                    [PDimg, CBFimg] = ASL_CBF(path, maskStatus, 1:firstRow);
        
                    displayImages(app.UIAxes_2row_1, PDimg, 'gray', '');
                    CBFimage_display(app.UIAxes_2row_3, CBFimg*1.5, [0 400], 'jet', '');
        
                    % Standardizing color scale
                    colorScale = clim(app.UIAxes_2row_1);
                    clim(app.UIAxes_2row_2, colorScale);
                    
                    % GRAPHING
                    [PDimg, CBFimg] = ASL_CBF(path, maskStatus, firstRow+1:Nslice);
        
                    displayImages(app.UIAxes_2row_2, PDimg, 'gray', '');
                    CBFimage_display(app.UIAxes_2row_4, CBFimg*1.5, [0 400], 'jet', '');
           
                  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
                    
                case '3 Rows'
                    totalRows = 3;
                    eachRow = ceil(Nslice / totalRows);
        
                    % GRAPHING
                    [PDimg, CBFimg] = ASL_CBF(path, maskStatus, 1:eachRow);
                 
                    displayImages(app.UIAxes_3row_1, PDimg, 'gray', '');
                    CBFimage_display(app.UIAxes_3row_4, CBFimg*1.5, [0 400], 'jet', '');
        
                    % Standardizing color scale
                    colorScale = clim(app.UIAxes_3row_1);
                    clim(app.UIAxes_3row_2, colorScale);
                    clim(app.UIAxes_3row_3, colorScale);
        
                    % DISPLAYING ROW 2
                    nextRow = eachRow + eachRow;
        
                    % GRAPHING
                    [PDimg, CBFimg] = ASL_CBF(path, maskStatus, eachRow+1:nextRow);
        
                    displayImages(app.UIAxes_3row_2, PDimg, 'gray', '');
                    CBFimage_display(app.UIAxes_3row_5, CBFimg*1.5, [0 400], 'jet', '');
        
                    % DISPLAYING ROW 3
                    [PDimg, CBFimg] = ASL_CBF(path, maskStatus, nextRow+1:Nslice);
        
                    displayImages(app.UIAxes_3row_3, PDimg, 'gray', '');
                    CBFimage_display(app.UIAxes_3row_6, CBFimg*1.5, [0 400], 'jet', '');
           
            end
                    
            % Changes button visibility
            app.ConfirmandDisplayButton.Visible = 'off';
            app.CLEARButton.Visible = 'on';
            
        end

        % Button pushed function: CLEARButton
        function CLEARButtonPushed(app, event)
            % Clears display options screen after each display
            clearOptionsAxes(app);

        end

        % Button pushed function: STARTButton
        function STARTButtonPushed(app, event)
         try 
            maskStatus = 0;

            % Getting path and Nslice
            path = app.YourdirectoryEditField.Value;

            nslicePath = [path, filesep, 'ASL.mat'];
            load(nslicePath, 'diffmap')
            Nslice = size(diffmap, 3);
            
            maskpath = fullfile(path, 'MASK');

            % UI
            app.STARTButton.Visible = 'off';
            app.instructionLabel.Visible = 'on';
            app.instructionLabel2.Visible = 'on';
    
           % Loop through each image, letting the user mask each time
            i = 1;
            while i <= Nslice

                % Clear original image every iteration
                cla(app.originalImage);
               
                if app.maskNumberStart <= Nslice

                    [PDimg, ~] = ASL_CBF(path, maskStatus, app.maskNumberStart:app.maskNumberStart);
            
                    % Makes the original image
                    imagesc(app.originalImage, PDimg)
                    colorbar(app.originalImage,'location','Eastoutside','FontSize', 18)
                    colormap(app.originalImage, 'gray');
                    axis(app.originalImage, 'image');
                    axis (app.originalImage, 'off');
                    hold (app.originalImage, 'on');
      
                end     
                % Letting user draw the mask
                a = drawpolygon(app.originalImage);
                
                % Creates mask and saves binary array data
                mask = createMask(a);
    
                % Initializes empty array
                if i == 1
                    ROI = zeros(size(mask, 1), size(mask, 2), Nslice);
                end
    
                ROI(:,:, app.maskNumberStart) = mask;
         
               % Displaying the masked image
                maskedImage = PDimg;
                maskedImage(:, :, 1) = maskedImage(:, :, 1) .* mask;
    
                % Set the area outside the polygon to black
                maskedImage(~mask) = 0;
    
                % Display the mask
                cla(app.maskImage); 
                imagesc(maskedImage, 'Parent', app.maskImage);
                colorbar(app.maskImage, 'location', 'Eastoutside', 'FontSize', 18);
                colormap(app.maskImage, 'gray');
                axis(app.maskImage, 'image');
                axis(app.maskImage, 'off');
                hold(app.maskImage, 'on');
               
               % Iteration updates
                app.maskNumberStart = app.maskNumberStart + 1;
    
                i = i+1;
            end
            
            save(maskpath, "ROI");
           
            % Clears the original/masked images to display CBF
            cla(app.maskImage);
            cla(app.originalImage);
            colorbar(app.maskImage, 'off');
            colorbar(app.originalImage, 'off');
            app.maskImage.Title.Visible = 'off';
            app.originalImage.Title.Visible = 'off';

            maskPath = [path, filesep, 'MASK.mat'];
            
            if isfile(maskPath)
                maskStatus = 1;
            end

            [~, CBFimg] = ASL_CBF(path, maskStatus, 1:Nslice);
            CBFimage_display(app.displayMASK, CBFimg*1.5, [0 400], 'jet', '');
            
            % UI update
            app.instructionLabel.Visible = 'off';
            app.instructionLabel2.Visible = 'off';
            app.MASKINGCOMPLETELabel.Visible = 'on';
            app.returnHomeButton2.Visible = 'on';
            app.RestartButton.Visible = 'on';
 
        catch
            a = msgbox("An error occurred. Please restart");
            pause(2.5)
            try
                close(a)
            end
            app.RestartButton.Visible = 'on';
            figure(app.UIFigure);
        end

        end

        % Button pushed function: returnHomeButton2
        function returnHomeButton2Pushed(app, event)
            % Changing tabs
            app.TabGroup.SelectedTab = app.HomeTab;

        end

        % Button pushed function: MaskButton
        function MaskButtonPushed(app, event)
            % Changing tabs
            app.TabGroup.SelectedTab = app.MaskTab;

        end

        % Button pushed function: RestartButton
        function RestartButtonPushed(app, event)
            % Clears the "Mask" tab for reuse
            clearMaskTab(app);

        end
    end

    % Component initialization
    methods (Access = private)

        % Create UIFigure and components
        function createComponents(app)

            % Get the file path for locating images
            pathToMLAPP = fileparts(mfilename('fullpath'));

            % Create UIFigure and hide until all components are created
            app.UIFigure = uifigure('Visible', 'off');
            app.UIFigure.Color = [0.8902 0.8706 0.9686];
            app.UIFigure.Position = [100 100 1010 828];
            app.UIFigure.Name = 'MATLAB App';

            % Create TabGroup
            app.TabGroup = uitabgroup(app.UIFigure);
            app.TabGroup.Position = [1 0 1009 829];

            % Create HomeTab
            app.HomeTab = uitab(app.TabGroup);
            app.HomeTab.Title = 'Home';
            app.HomeTab.BackgroundColor = [0.8902 0.8706 0.9686];

            % Create Axes1
            app.Axes1 = uiaxes(app.HomeTab);
            zlabel(app.Axes1, 'Z')
            app.Axes1.XTick = [];
            app.Axes1.YColor = 'none';
            app.Axes1.YTick = [];
            app.Axes1.Color = 'none';
            app.Axes1.Position = [62 300 533 316];

            % Create Axes2
            app.Axes2 = uiaxes(app.HomeTab);
            app.Axes2.XColor = [0 0 0];
            app.Axes2.XTick = [];
            app.Axes2.YColor = 'none';
            app.Axes2.YTick = [];
            app.Axes2.Color = 'none';
            app.Axes2.GridColor = [0 0 0];
            app.Axes2.Position = [62 4 533 298];

            % Create Image
            app.Image = uiimage(app.HomeTab);
            app.Image.Position = [343 638 357 168];
            app.Image.ImageSource = fullfile(pathToMLAPP, 'Kennedy_Krieger_Institute_logo.svg (1) copy.png');

            % Create StartAgainButton
            app.StartAgainButton = uibutton(app.HomeTab, 'push');
            app.StartAgainButton.ButtonPushedFcn = createCallbackFcn(app, @StartAgainButtonPushed, true);
            app.StartAgainButton.BackgroundColor = [0.9412 0.9412 0.9412];
            app.StartAgainButton.FontName = 'Times New Roman';
            app.StartAgainButton.FontSize = 14;
            app.StartAgainButton.Visible = 'off';
            app.StartAgainButton.Position = [771 20 97 53];
            app.StartAgainButton.Text = 'Start Again';

            % Create CBFDisplayButton
            app.CBFDisplayButton = uibutton(app.HomeTab, 'push');
            app.CBFDisplayButton.ButtonPushedFcn = createCallbackFcn(app, @CBFDisplayButtonPushed, true);
            app.CBFDisplayButton.BackgroundColor = [0.8196 0.749 0.9804];
            app.CBFDisplayButton.FontName = 'Times New Roman';
            app.CBFDisplayButton.FontSize = 14;
            app.CBFDisplayButton.Visible = 'off';
            app.CBFDisplayButton.Position = [729 191 185 59];
            app.CBFDisplayButton.Text = 'CBF Display';

            % Create PrepareButton
            app.PrepareButton = uibutton(app.HomeTab, 'push');
            app.PrepareButton.ButtonPushedFcn = createCallbackFcn(app, @PrepareButtonPushed, true);
            app.PrepareButton.BackgroundColor = [0.8196 0.749 0.9804];
            app.PrepareButton.FontName = 'Times New Roman';
            app.PrepareButton.FontSize = 15;
            app.PrepareButton.Visible = 'off';
            app.PrepareButton.Position = [729 384 185 59];
            app.PrepareButton.Text = 'Prepare';

            % Create ErrorLabel
            app.ErrorLabel = uilabel(app.HomeTab);
            app.ErrorLabel.FontName = 'Times New Roman';
            app.ErrorLabel.FontSize = 14;
            app.ErrorLabel.Visible = 'off';
            app.ErrorLabel.Position = [700 357 253 31];
            app.ErrorLabel.Text = 'An error has occurred. Please start again.';

            % Create PREPARATIONCOMPLETELabel
            app.PREPARATIONCOMPLETELabel = uilabel(app.HomeTab);
            app.PREPARATIONCOMPLETELabel.HorizontalAlignment = 'center';
            app.PREPARATIONCOMPLETELabel.FontName = 'Times New Roman';
            app.PREPARATIONCOMPLETELabel.FontSize = 13;
            app.PREPARATIONCOMPLETELabel.Visible = 'off';
            app.PREPARATIONCOMPLETELabel.Position = [736 357 180 31];
            app.PREPARATIONCOMPLETELabel.Text = 'PREPARATION COMPLETE';

            % Create SelectDirectoryButton
            app.SelectDirectoryButton = uibutton(app.HomeTab, 'push');
            app.SelectDirectoryButton.ButtonPushedFcn = createCallbackFcn(app, @SelectDirectoryButtonPushed, true);
            app.SelectDirectoryButton.BackgroundColor = [0.8196 0.749 0.9804];
            app.SelectDirectoryButton.FontName = 'Times New Roman';
            app.SelectDirectoryButton.FontSize = 15;
            app.SelectDirectoryButton.Position = [729 526 185 59];
            app.SelectDirectoryButton.Text = 'Select Directory';

            % Create WelcomePleaseselectyourdirectoryLabel
            app.WelcomePleaseselectyourdirectoryLabel = uilabel(app.HomeTab);
            app.WelcomePleaseselectyourdirectoryLabel.HorizontalAlignment = 'center';
            app.WelcomePleaseselectyourdirectoryLabel.FontName = 'Times New Roman';
            app.WelcomePleaseselectyourdirectoryLabel.FontSize = 18;
            app.WelcomePleaseselectyourdirectoryLabel.FontAngle = 'italic';
            app.WelcomePleaseselectyourdirectoryLabel.FontColor = [0.3529 0.1686 0.3882];
            app.WelcomePleaseselectyourdirectoryLabel.Position = [667 588 305 35];
            app.WelcomePleaseselectyourdirectoryLabel.Text = 'Welcome. Please select your directory';

            % Create YourdirectoryEditFieldLabel
            app.YourdirectoryEditFieldLabel = uilabel(app.HomeTab);
            app.YourdirectoryEditFieldLabel.HorizontalAlignment = 'center';
            app.YourdirectoryEditFieldLabel.FontName = 'Times New Roman';
            app.YourdirectoryEditFieldLabel.Position = [780 463 81 22];
            app.YourdirectoryEditFieldLabel.Text = 'Your directory';

            % Create YourdirectoryEditField
            app.YourdirectoryEditField = uieditfield(app.HomeTab, 'text');
            app.YourdirectoryEditField.ValueChangedFcn = createCallbackFcn(app, @YourdirectoryEditFieldValueChanged, true);
            app.YourdirectoryEditField.HorizontalAlignment = 'center';
            app.YourdirectoryEditField.FontName = 'Times New Roman';
            app.YourdirectoryEditField.FontSize = 10;
            app.YourdirectoryEditField.BackgroundColor = [0.9412 0.9412 0.9412];
            app.YourdirectoryEditField.Position = [660 484 321 31];

            % Create MoreDisplayOptionsButton
            app.MoreDisplayOptionsButton = uibutton(app.HomeTab, 'push');
            app.MoreDisplayOptionsButton.ButtonPushedFcn = createCallbackFcn(app, @MoreDisplayOptionsButtonPushed, true);
            app.MoreDisplayOptionsButton.BackgroundColor = [0.9098 0.7098 1];
            app.MoreDisplayOptionsButton.FontName = 'Times New Roman';
            app.MoreDisplayOptionsButton.FontSize = 14;
            app.MoreDisplayOptionsButton.Visible = 'off';
            app.MoreDisplayOptionsButton.Position = [729 92 185 59];
            app.MoreDisplayOptionsButton.Text = 'More Display Options';

            % Create MaskButton
            app.MaskButton = uibutton(app.HomeTab, 'push');
            app.MaskButton.ButtonPushedFcn = createCallbackFcn(app, @MaskButtonPushed, true);
            app.MaskButton.BackgroundColor = [0.8196 0.749 0.9804];
            app.MaskButton.FontName = 'Times New Roman';
            app.MaskButton.FontSize = 15;
            app.MaskButton.Visible = 'off';
            app.MaskButton.Position = [729 284 185 59];
            app.MaskButton.Text = 'Mask';

            % Create PleaseWaitLabel
            app.PleaseWaitLabel = uilabel(app.HomeTab);
            app.PleaseWaitLabel.HorizontalAlignment = 'center';
            app.PleaseWaitLabel.FontName = 'Times New Roman';
            app.PleaseWaitLabel.FontSize = 13;
            app.PleaseWaitLabel.Visible = 'off';
            app.PleaseWaitLabel.Position = [736 357 180 31];
            app.PleaseWaitLabel.Text = 'Please Wait';

            % Create DisplayOptionsTab
            app.DisplayOptionsTab = uitab(app.TabGroup);
            app.DisplayOptionsTab.Title = 'Display Options';
            app.DisplayOptionsTab.BackgroundColor = [0.8902 0.8706 0.9686];

            % Create UIAxes_1row
            app.UIAxes_1row = uiaxes(app.DisplayOptionsTab);
            zlabel(app.UIAxes_1row, 'Z')
            app.UIAxes_1row.XColor = 'none';
            app.UIAxes_1row.XTick = [];
            app.UIAxes_1row.YColor = 'none';
            app.UIAxes_1row.YTick = [];
            app.UIAxes_1row.Color = 'none';
            app.UIAxes_1row.Position = [48 373 910 328];

            % Create UIAxes_1row_2
            app.UIAxes_1row_2 = uiaxes(app.DisplayOptionsTab);
            zlabel(app.UIAxes_1row_2, 'Z')
            app.UIAxes_1row_2.XColor = 'none';
            app.UIAxes_1row_2.XTick = [];
            app.UIAxes_1row_2.YColor = 'none';
            app.UIAxes_1row_2.YTick = [];
            app.UIAxes_1row_2.Color = 'none';
            app.UIAxes_1row_2.Position = [48 9 910 330];

            % Create UIAxes_2row_1
            app.UIAxes_2row_1 = uiaxes(app.DisplayOptionsTab);
            zlabel(app.UIAxes_2row_1, 'Z')
            app.UIAxes_2row_1.XColor = 'none';
            app.UIAxes_2row_1.XTick = [];
            app.UIAxes_2row_1.YColor = 'none';
            app.UIAxes_2row_1.YTick = [];
            app.UIAxes_2row_1.Color = 'none';
            app.UIAxes_2row_1.Position = [53 545 914 157];

            % Create UIAxes_2row_2
            app.UIAxes_2row_2 = uiaxes(app.DisplayOptionsTab);
            zlabel(app.UIAxes_2row_2, 'Z')
            app.UIAxes_2row_2.XColor = 'none';
            app.UIAxes_2row_2.XTick = [];
            app.UIAxes_2row_2.YColor = 'none';
            app.UIAxes_2row_2.YTick = [];
            app.UIAxes_2row_2.Color = 'none';
            app.UIAxes_2row_2.Position = [53 366 914 157];

            % Create UIAxes_2row_3
            app.UIAxes_2row_3 = uiaxes(app.DisplayOptionsTab);
            zlabel(app.UIAxes_2row_3, 'Z')
            app.UIAxes_2row_3.XColor = 'none';
            app.UIAxes_2row_3.XTick = [];
            app.UIAxes_2row_3.YColor = 'none';
            app.UIAxes_2row_3.YTick = [];
            app.UIAxes_2row_3.Color = 'none';
            app.UIAxes_2row_3.Position = [53 190 914 157];

            % Create UIAxes_2row_4
            app.UIAxes_2row_4 = uiaxes(app.DisplayOptionsTab);
            zlabel(app.UIAxes_2row_4, 'Z')
            app.UIAxes_2row_4.XColor = 'none';
            app.UIAxes_2row_4.XTick = [];
            app.UIAxes_2row_4.YColor = 'none';
            app.UIAxes_2row_4.YTick = [];
            app.UIAxes_2row_4.Color = 'none';
            app.UIAxes_2row_4.Position = [53 9 914 157];

            % Create UIAxes_3row_1
            app.UIAxes_3row_1 = uiaxes(app.DisplayOptionsTab);
            zlabel(app.UIAxes_3row_1, 'Z')
            app.UIAxes_3row_1.XColor = 'none';
            app.UIAxes_3row_1.XTick = [];
            app.UIAxes_3row_1.YColor = 'none';
            app.UIAxes_3row_1.YTick = [];
            app.UIAxes_3row_1.Color = 'none';
            app.UIAxes_3row_1.Position = [126 598 788 103];

            % Create UIAxes_3row_2
            app.UIAxes_3row_2 = uiaxes(app.DisplayOptionsTab);
            zlabel(app.UIAxes_3row_2, 'Z')
            app.UIAxes_3row_2.XColor = 'none';
            app.UIAxes_3row_2.XTick = [];
            app.UIAxes_3row_2.YColor = 'none';
            app.UIAxes_3row_2.YTick = [];
            app.UIAxes_3row_2.Color = 'none';
            app.UIAxes_3row_2.Position = [125 481 788 103];

            % Create UIAxes_3row_3
            app.UIAxes_3row_3 = uiaxes(app.DisplayOptionsTab);
            zlabel(app.UIAxes_3row_3, 'Z')
            app.UIAxes_3row_3.XColor = 'none';
            app.UIAxes_3row_3.XTick = [];
            app.UIAxes_3row_3.YColor = 'none';
            app.UIAxes_3row_3.YTick = [];
            app.UIAxes_3row_3.Color = 'none';
            app.UIAxes_3row_3.Position = [126 366 788 103];

            % Create UIAxes_3row_4
            app.UIAxes_3row_4 = uiaxes(app.DisplayOptionsTab);
            zlabel(app.UIAxes_3row_4, 'Z')
            app.UIAxes_3row_4.XColor = 'none';
            app.UIAxes_3row_4.XTick = [];
            app.UIAxes_3row_4.YColor = 'none';
            app.UIAxes_3row_4.YTick = [];
            app.UIAxes_3row_4.Color = 'none';
            app.UIAxes_3row_4.Position = [126 236 788 103];

            % Create UIAxes_3row_5
            app.UIAxes_3row_5 = uiaxes(app.DisplayOptionsTab);
            zlabel(app.UIAxes_3row_5, 'Z')
            app.UIAxes_3row_5.XColor = 'none';
            app.UIAxes_3row_5.XTick = [];
            app.UIAxes_3row_5.YColor = 'none';
            app.UIAxes_3row_5.YTick = [];
            app.UIAxes_3row_5.Color = 'none';
            app.UIAxes_3row_5.Position = [126 120 788 103];

            % Create UIAxes_3row_6
            app.UIAxes_3row_6 = uiaxes(app.DisplayOptionsTab);
            zlabel(app.UIAxes_3row_6, 'Z')
            app.UIAxes_3row_6.XColor = 'none';
            app.UIAxes_3row_6.XTick = [];
            app.UIAxes_3row_6.YColor = 'none';
            app.UIAxes_3row_6.YTick = [];
            app.UIAxes_3row_6.Color = 'none';
            app.UIAxes_3row_6.Position = [126 5 788 103];

            % Create SelectNumberofRowstoDisplayLabel
            app.SelectNumberofRowstoDisplayLabel = uilabel(app.DisplayOptionsTab);
            app.SelectNumberofRowstoDisplayLabel.HorizontalAlignment = 'center';
            app.SelectNumberofRowstoDisplayLabel.FontName = 'Times New Roman';
            app.SelectNumberofRowstoDisplayLabel.FontSize = 15;
            app.SelectNumberofRowstoDisplayLabel.Position = [170 774 224 22];
            app.SelectNumberofRowstoDisplayLabel.Text = 'Select Number of Rows to Display :';

            % Create NumberofRowstoDisplayDropDown
            app.NumberofRowstoDisplayDropDown = uidropdown(app.DisplayOptionsTab);
            app.NumberofRowstoDisplayDropDown.Items = {'1 Row', '2 Rows', '3 Rows'};
            app.NumberofRowstoDisplayDropDown.FontName = 'Times New Roman';
            app.NumberofRowstoDisplayDropDown.FontSize = 15;
            app.NumberofRowstoDisplayDropDown.Position = [409 774 459 22];
            app.NumberofRowstoDisplayDropDown.Value = '1 Row';

            % Create ConfirmandDisplayButton
            app.ConfirmandDisplayButton = uibutton(app.DisplayOptionsTab, 'push');
            app.ConfirmandDisplayButton.ButtonPushedFcn = createCallbackFcn(app, @ConfirmandDisplayButtonPushed, true);
            app.ConfirmandDisplayButton.BackgroundColor = [0.8392 0.7804 0.9804];
            app.ConfirmandDisplayButton.FontName = 'Times New Roman';
            app.ConfirmandDisplayButton.FontSize = 14;
            app.ConfirmandDisplayButton.Position = [467 713 154 49];
            app.ConfirmandDisplayButton.Text = 'Confirm and Display';

            % Create ReturnHomeButton
            app.ReturnHomeButton = uibutton(app.DisplayOptionsTab, 'push');
            app.ReturnHomeButton.ButtonPushedFcn = createCallbackFcn(app, @ReturnHomeButtonPushed, true);
            app.ReturnHomeButton.BackgroundColor = [0.7882 0.9216 1];
            app.ReturnHomeButton.FontSize = 16;
            app.ReturnHomeButton.FontWeight = 'bold';
            app.ReturnHomeButton.Position = [22 736 51 48];
            app.ReturnHomeButton.Text = '<--';

            % Create CLEARButton
            app.CLEARButton = uibutton(app.DisplayOptionsTab, 'push');
            app.CLEARButton.ButtonPushedFcn = createCallbackFcn(app, @CLEARButtonPushed, true);
            app.CLEARButton.BackgroundColor = [0.9882 0.7882 0.7882];
            app.CLEARButton.FontName = 'Times New Roman';
            app.CLEARButton.FontSize = 14;
            app.CLEARButton.Visible = 'off';
            app.CLEARButton.Position = [468 713 154 49];
            app.CLEARButton.Text = 'CLEAR';

            % Create MaskTab
            app.MaskTab = uitab(app.TabGroup);
            app.MaskTab.Title = 'Mask';
            app.MaskTab.BackgroundColor = [0.8902 0.8706 0.9686];

            % Create originalImage
            app.originalImage = uiaxes(app.MaskTab);
            title(app.originalImage, 'Image ')
            zlabel(app.originalImage, 'Z')
            app.originalImage.XColor = 'none';
            app.originalImage.XTick = [];
            app.originalImage.YColor = 'none';
            app.originalImage.YTick = [];
            app.originalImage.ZColor = 'none';
            app.originalImage.Color = 'none';
            app.originalImage.GridColor = [0.149 0.149 0.149];
            app.originalImage.Position = [26 284 473 432];

            % Create maskImage
            app.maskImage = uiaxes(app.MaskTab);
            title(app.maskImage, 'Masked Image')
            zlabel(app.maskImage, 'Z')
            app.maskImage.XColor = 'none';
            app.maskImage.XTick = [];
            app.maskImage.YColor = 'none';
            app.maskImage.YTick = [];
            app.maskImage.ZColor = 'none';
            app.maskImage.Color = 'none';
            app.maskImage.GridColor = [0.149 0.149 0.149];
            app.maskImage.Position = [529 284 473 432];

            % Create displayMASK
            app.displayMASK = uiaxes(app.MaskTab);
            zlabel(app.displayMASK, 'Z')
            app.displayMASK.XColor = 'none';
            app.displayMASK.XTick = [];
            app.displayMASK.YColor = 'none';
            app.displayMASK.YTick = [];
            app.displayMASK.Color = 'none';
            app.displayMASK.Position = [10 284 988 463];

            % Create STARTButton
            app.STARTButton = uibutton(app.MaskTab, 'push');
            app.STARTButton.ButtonPushedFcn = createCallbackFcn(app, @STARTButtonPushed, true);
            app.STARTButton.BackgroundColor = [0.8196 0.749 0.9804];
            app.STARTButton.FontName = 'Times New Roman';
            app.STARTButton.FontSize = 14;
            app.STARTButton.Position = [452 106 159 64];
            app.STARTButton.Text = 'START';

            % Create instructionLabel
            app.instructionLabel = uilabel(app.MaskTab);
            app.instructionLabel.FontName = 'Times New Roman';
            app.instructionLabel.FontSize = 14;
            app.instructionLabel.Visible = 'off';
            app.instructionLabel.Position = [28 240 496 45];
            app.instructionLabel.Text = 'Click to draw vertices of the polygon and drag to draw the lines between the vertices. ';

            % Create MASKINGCOMPLETELabel
            app.MASKINGCOMPLETELabel = uilabel(app.MaskTab);
            app.MASKINGCOMPLETELabel.FontName = 'Times New Roman';
            app.MASKINGCOMPLETELabel.FontSize = 21;
            app.MASKINGCOMPLETELabel.Visible = 'off';
            app.MASKINGCOMPLETELabel.Position = [422 189 220 39];
            app.MASKINGCOMPLETELabel.Text = 'MASKING COMPLETE';

            % Create returnHomeButton2
            app.returnHomeButton2 = uibutton(app.MaskTab, 'push');
            app.returnHomeButton2.ButtonPushedFcn = createCallbackFcn(app, @returnHomeButton2Pushed, true);
            app.returnHomeButton2.BackgroundColor = [0.7882 0.9216 1];
            app.returnHomeButton2.FontSize = 16;
            app.returnHomeButton2.FontWeight = 'bold';
            app.returnHomeButton2.Position = [37 28 64 49];
            app.returnHomeButton2.Text = '<--';

            % Create RestartButton
            app.RestartButton = uibutton(app.MaskTab, 'push');
            app.RestartButton.ButtonPushedFcn = createCallbackFcn(app, @RestartButtonPushed, true);
            app.RestartButton.BackgroundColor = [0.9098 0.7098 1];
            app.RestartButton.FontName = 'Times New Roman';
            app.RestartButton.FontSize = 15;
            app.RestartButton.Visible = 'off';
            app.RestartButton.Position = [452 20 159 64];
            app.RestartButton.Text = 'Restart';

            % Create instructionLabel2
            app.instructionLabel2 = uilabel(app.MaskTab);
            app.instructionLabel2.FontName = 'Times New Roman';
            app.instructionLabel2.FontSize = 16;
            app.instructionLabel2.Visible = 'off';
            app.instructionLabel2.Position = [160 212 210 22];
            app.instructionLabel2.Text = 'To finish the ROI, double-click.';

            % Create Label_2
            app.Label_2 = uilabel(app.MaskTab);
            app.Label_2.Position = [727 248 25 22];
            app.Label_2.Text = '';

            % Show the figure after all components are created
            app.UIFigure.Visible = 'on';
        end
    end

    % App creation and deletion
    methods (Access = public)

        % Construct app
        function app = ASL_ProjectCode

            % Create UIFigure and components
            createComponents(app)

            % Register the app with App Designer
            registerApp(app, app.UIFigure)

            if nargout == 0
                clear app
            end
        end

        % Code that executes before app deletion
        function delete(app)

            % Delete UIFigure when app is deleted
            delete(app.UIFigure)
        end
    end
end