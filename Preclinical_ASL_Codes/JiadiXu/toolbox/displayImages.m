% Displays image on UI Axes based on input information

function displayImages(axes, imageMatrix, colorMap, titleText)
    
    imagesc(axes, imageMatrix);
    colorbar(axes,'location','Eastoutside','FontSize', 18)
    colormap(axes, colorMap);
    title(axes, titleText)
    axis(axes, 'image');

end
            
           
            