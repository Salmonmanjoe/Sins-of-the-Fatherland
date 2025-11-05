using Godot;
using System;
using System.ComponentModel.Design;

public partial class SetupUI : Control
{
	[Export]
	public NodePath InventoryNodePath;
	[Export]
	public NodePath MapNodePath;
	[Export]
	public NodePath SpellsNodePath;
	[Export]
	public NodePath StatNodePath;
	[Export]
	public NodePath MenuNodePath;

	private InventoryScript inventory;
	private MapScript map;
	private SpellsWindowScript spell;
	private MenuTabBar menuTabBar;
	private StatScript stat;


	public override void _Ready()
	{
		//Connect to the tab bar and buttons
		menuTabBar = GetNode<MenuTabBar>(MenuNodePath);
		if (menuTabBar != null)
		{
			menuTabBar.Connect(MenuTabBar.SignalName.Tab1Clicked, new Callable(this, nameof(OnTab1Clicked)));
			menuTabBar.Connect(MenuTabBar.SignalName.Tab2Clicked, new Callable(this, nameof(OnTab2Clicked)));
			menuTabBar.Connect(MenuTabBar.SignalName.Tab3Clicked, new Callable(this, nameof(OnTab3Clicked)));
			menuTabBar.Connect(MenuTabBar.SignalName.Tab4Clicked, new Callable(this, nameof(OnTab4Clicked)));
		}
		else
		{
			GD.PushWarning("Menu tab node not found. Make sure TabBar is set.");
		}

		// Connect to inventory window
		inventory = GetNode<InventoryScript>(InventoryNodePath);

		if (inventory != null)
		{
			inventory.Connect(InventoryScript.SignalName.InventoryBool, new Callable(this, nameof(OnInventoryClosed)));
			//inventory.Connect(InventoryScript.SignalName.InventoryOpened, new Callable(this, nameof(OnInventoryOpened)));//this doesn't really work lol
		}
		else
		{
			GD.PushWarning("Inventory node not found. Make sure InventoryNodePath is set.");
		}

		// Connect to inventory window
		map = GetNode<MapScript>(MapNodePath);

		if (map != null)
		{
			map.Connect(MapScript.SignalName.MapBool, new Callable(this, nameof(OnMapToggled)));
		}
		else
		{
			GD.PushWarning("Map node not found. Make sure MapNodePath is set.");
		}

		// Connect to inventory window
		spell = GetNode<SpellsWindowScript>(SpellsNodePath);

		if (spell != null)
		{
			spell.Connect(SpellsWindowScript.SignalName.SpellsBool, new Callable(this, nameof(OnSpellsToggled)));
		}
		else
		{
			GD.PushWarning("Spells node not found. Make sure SpellsNodePath is set.");
		}
		stat = GetNode<StatScript>(StatNodePath);

		if (stat != null)
		{
			stat.Connect(StatScript.SignalName.StatBool, new Callable(this, nameof(OnStatToggled)));
		}
		else
		{
			GD.PushWarning("Stats node not found. Make sure StatNodePath is set.");
		}
	}

	private void OnInventoryClosed()
	{
		GD.Print("Inventory closed signal received.");
	}
	private void OnMapToggled()
	{
		GD.Print("Map closed signal received.");
	}
	private void OnSpellsToggled()
	{
		GD.Print("Spells closed signal received.");
	}
	private void OnStatToggled()
	{
		GD.Print("Stats closed signal received.");
	}

	private void OnTab1Clicked()
	{
		GD.Print("Inventory button clicked");
		inventory.Visible = !inventory.Visible;
	}
	private void OnTab2Clicked()
	{
		GD.Print("Map button clicked");
		map.Visible = !map.Visible;
	}
	private void OnTab3Clicked()
	{
		GD.Print("Spells button clicked");
		spell.Visible = !spell.Visible;
	}
	private void OnTab4Clicked()
	{
		GD.Print("Spells button clicked");
		stat.Visible = !stat.Visible;
	}
}
