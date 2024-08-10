
% Displays CBF images on UI Axes based on user input
    
    function CBFimage_display(axes, image, climRange, colorMap, titleText)
        
        imagesc(axes, image, climRange);
        colorbar(axes, 'location', 'Eastoutside', 'FontSize', 18);
        title(axes, titleText);
        colormap(axes, colorMap);
        axis(axes, 'image');
        axis(axes, 'off');
        hold(axes, 'off');

    end





