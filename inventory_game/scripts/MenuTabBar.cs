using Godot;
using System;

public partial class MenuTabBar : TabBar
{
	[Export] public TabBar TabBar { get; set; }

	// Define signals for each tab
	[Signal] public delegate void Tab1ClickedEventHandler();
	[Signal] public delegate void Tab2ClickedEventHandler();
	[Signal] public delegate void Tab3ClickedEventHandler();
	[Signal] public delegate void Tab4ClickedEventHandler();

	public override void _Ready()
	{
		if (TabBar != null)
		{
			// Connect TabBar’s built-in signal
			TabBar.TabClicked += OnTabClicked;
		}
	}

	private void OnTabClicked(long tabIndex)
	{
		switch (tabIndex)
		{
			case 0:
				EmitSignal(SignalName.Tab1Clicked);
				GD.Print("Tab 1 Clicked");
				break;
			case 1:
				EmitSignal(SignalName.Tab2Clicked);
				GD.Print("Tab 2 Clicked");
				break;
			case 2:
				EmitSignal(SignalName.Tab3Clicked);
				GD.Print("Tab 3 Clicked");
				break;
			case 3:
				EmitSignal(SignalName.Tab4Clicked);
				GD.Print("Tab 4 Clicked");
				break;
		}
	}
}
