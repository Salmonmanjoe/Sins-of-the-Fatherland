using Godot;
using System;

public partial class StatScript : Window
{
	[Signal]
	public delegate void StatBoolEventHandler(); //inv interacted with

	public override void _Ready()
	{
		// Connect the CloseRequested signal to our handler method
		CloseRequested += OnCloseRequested;
	}

	private void OnCloseRequested()
	{
		GD.Print("Stat close button clicked");
		// Minimize the window instead of closing it
		this.Visible = false;
		EmitSignal(SignalName.StatBool);
	}
}
