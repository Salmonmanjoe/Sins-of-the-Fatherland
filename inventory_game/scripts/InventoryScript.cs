using Godot;
using System;

public partial class InventoryScript : Window
{
	[Signal]
	public delegate void InventoryBoolEventHandler(); //inv interacted with

	public override void _Ready()
	{
		// Connect the CloseRequested signal to our handler method
		CloseRequested += OnCloseRequested;
		ContentScaleAspect = ContentScaleAspectEnum.Ignore;

		Window window = GetWindow();
		window.SizeChanged += OnWindowSizeChanged;
		UpdateControlToWindow(window);
	}



	private void OnCloseRequested()
	{
		GD.Print("Inventory close button clicked");
		// Minimize the window instead of closing it
		this.Visible = false;
		EmitSignal(SignalName.InventoryBool);
	}
	
	

    private void OnWindowSizeChanged()
    {
        UpdateControlToWindow(GetWindow());
    }

    private void UpdateControlToWindow(Window window)
    {
        //Rect2 contentRect = window.GetContentRect();

        // Match the Control's position and size to the window's inner corners
        //Position = contentRect.Position;
        //Size = contentRect.Size;
    }
}
