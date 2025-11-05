using Godot;
using System;

public partial class SpellsWindowScript : Window
{
	[Signal]
	public delegate void SpellsBoolEventHandler(); //inv interacted with

	public override void _Ready()
	{
		// Connect the CloseRequested signal to our handler method
		CloseRequested += OnCloseRequested;
	}

	private void OnCloseRequested()
	{
		GD.Print("Spells close button clicked");
		// Minimize the window instead of closing it
		this.Visible = false;
		EmitSignal(SignalName.SpellsBool);
	}
}
