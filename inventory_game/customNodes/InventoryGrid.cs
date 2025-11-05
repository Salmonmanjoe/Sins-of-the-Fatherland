using Godot;
using System;
using Godot.Collections;
using System.Collections.Generic;
using System.Text.Json;

[GlobalClass] //should make the script appear in add node menu
public partial class InventoryGrid : TextureRect
{
	[Export] public bool onLoad { get; set; } = false;
	[Export] public string saveFilePath { get; set; } = "res://saved_data.dat";
	[Export] public ItemDataBase Data { get; set; }


	[ExportCategory("Grid")]
	[Export] public int CellSize { get; set; } = 32;
	[Export(PropertyHint.Range, "1,999,1")] public int GridHeight { get; set; } = 8;
	[Export(PropertyHint.Range, "1,999,1")] public int GridWidth { get; set; } = 8;
	[Export] public Texture2D HoverTexture { get; set; }

	// Runtime vars
	public TextureRect HoverRect { get; private set; }
	public ItemBase ItemHeld { get; private set; } = null;
	public Vector2 Offset { get; set; } = Vector2.Zero;
	public Vector2 MousePos { get; set; } = Vector2.Zero;
	public Vector2I ItemLastPosition { get; set; } = Vector2I.Zero;

	public List<Dictionary> SavedItems { get; private set; } = new();
	public List<Node> Inventories { get; private set; } = new();

	// Signals
	[Signal] public delegate void FocusGridMovedEventHandler();
	[Signal] public delegate void ItemRotatedEventHandler();
	[Signal] public delegate void ItemSwappedEventHandler();
	

	// ------------------- Lifecycle ------------------- //
	public override void _EnterTree()
	{
		AddToGroup("grid_inventory");
	}

	public override void _Ready()
	{
		StretchMode = StretchModeEnum.Tile;
		CustomMinimumSize = new Vector2I(CellSize * GridHeight, CellSize * GridWidth);

		// Create hover rect
		var hoverChild = new TextureRect
		{
			Texture = HoverTexture,
			Size = new Vector2I(CellSize, CellSize)
		};
		AddChild(hoverChild);
		HoverRect = hoverChild;

		if (onLoad)
			LoadItems();

		Inventories = new List<Node>(GetTree().GetNodesInGroup("grid_inventory"));
	}

	public override void _Process(double delta)
	{
		CustomMinimumSize = new Vector2I(CellSize * GridHeight, CellSize * GridWidth);

		if (!Engine.IsEditorHint())
		{
			MousePos = GetGlobalMousePosition();
			HoverMouse();

			if (Input.IsActionJustPressed("mouse1"))
			{
				if (ItemHeld == null)
					Grab();
				else
					Release();
			}

			if (ItemHeld != null)
				ItemHeld.GlobalPosition = MousePos - ItemHeld.Size / 2;
		}
	}

	// ------------------- Hover ------------------- //
	private void HoverMouse()
	{
		if (GetGlobalRect().HasPoint(MousePos))
		{
			Vector2 resultPosition = Vector2.Zero;
			Vector2 prevPosition = HoverRect.Position;
			Vector2 snapper;

			if (ItemHeld == null)
				snapper = ((MousePos - GlobalPosition) - (new Vector2(CellSize, CellSize) / 2));
			else
				snapper = (ItemHeld.GlobalPosition - GlobalPosition);

			resultPosition = snapper.Snapped(new Vector2(CellSize, CellSize));
			HoverRect.Position = resultPosition.Clamp(Vector2.Zero, Size);

			if (resultPosition != prevPosition)
				EmitSignal(SignalName.FocusGridMoved);
		}
	}

	// ------------------- Item Handling ------------------- //
	public ItemData GetItem(string itemId)
	{
		foreach (var item in Data.Items)
		{
			if (item.Name == itemId)
				return item;
		}

		var errorItem = new ItemData
		{
			Name = "error",
			Icon = GD.Load<CompressedTexture2D>("uid://b1s5lq76hs3e0")
		};
		GD.PrintErr("item: ", itemId, " is not found!");
		return errorItem;
	}

	public bool AddItem(string itemId = "", int quantity = 1)
	{
		var rect = GetGlobalRect();
		var itemData = GetItem(itemId);

		for (int line = (int)rect.Position.Y; line < rect.End.Y; line += CellSize)
		{
			for (int column = (int)rect.Position.X; column < rect.End.X; column += CellSize)
			{
				Vector2I placePoint = new Vector2I(column, line);
				Rect2 area = new Rect2(placePoint, (Vector2)(itemData.GridSize * CellSize));

				// stacking
				if (itemData.Stackable)
				{
					foreach (ItemBase itm in GetItems())
					{
						if (itm.ItemData.Name == itemId)
						{
							itm.Quantity += quantity;
							return true;
						}
					}
				}

				if (AreaIsClear(area, new Godot.Collections.Array { ItemHeld }))
				{
					var itemInstance = new ItemBase();
					AddChild(itemInstance);
					itemInstance.PrepItem(itemData);
					itemInstance.GlobalPosition = placePoint;

					return true;
				}
			}
		}

		GD.PrintErr("Could not place item, inventory full");
		return false;
	}

	public void SaveItems()
	{
		SavedItems.Clear();
		foreach (ItemBase item in GetItems())
		{
			var saveData = new Dictionary
			{
				{"name", item.ItemData.Name},
				{"pos", item.Position},
				{"qty", item.Quantity},
				{"rotated", item.IsRotated}
			};
			SavedItems.Add(saveData);
		}
		GD.Print(SavedItems);

		SaveToFile(SavedItems, saveFilePath);
	}

	public void LoadItems()
	{
		SavedItems = LoadFromFile(saveFilePath);

		foreach (var itemDict in SavedItems)
		{
			var itemInstance = new ItemBase();
			AddChild(itemInstance);

			var itemData = GetItem(itemDict["name"].AsString());
			itemInstance.PrepItem(itemData);

			itemInstance.Position = (Vector2I)itemDict["pos"];
			itemInstance.Quantity = (int)itemDict["qty"];

			if ((bool)itemDict["rotated"])
				itemInstance.Rotate();
		}
	}

	private void Grab()
	{
		if (ItemHeld != null) return;

		if (!LocationIsClear(MousePos) && GetGlobalRect().HasPoint(MousePos))
		{
			foreach (ItemBase cell in GetItems())
			{
				if (cell.GetGlobalRect().HasPoint(MousePos))
				{
					ItemHeld = cell;
					Offset = cell.GlobalPosition - MousePos;
					MoveChild(ItemHeld, GetChildCount()); // bring to front
					ItemLastPosition = (Vector2I)cell.GlobalPosition;
					ItemHeld.EmitSignal(ItemBase.SignalName.PickedUp);
					return;
				}
			}
		}
	}

	private void Release()
	{
		if (ItemHeld == null) return;

		Rect2 area = new Rect2(HoverRect.GlobalPosition, ItemHeld.GetGlobalRect().Size);

		// stacking logic
		foreach (ItemBase itm in GetItems())
		{
			if (itm != ItemHeld && itm.Stackable)
			{
				if (itm.GetGlobalRect().Intersects(area) && itm.ItemData.Name == ItemHeld.ItemData.Name)
				{
					itm.Quantity += ItemHeld.Quantity;
					ItemHeld.QueueFree();
					ItemHeld.EmitSignal(ItemBase.SignalName.PlacedDown);
					ItemHeld = null;
					return;
				}
			}
		}

		// invalid spot
		if (!IsAValidSpot(area))
		{
			ItemHeld.GlobalPosition = ItemLastPosition;
			ItemLastPosition = Vector2I.Zero;
			ItemHeld.EmitSignal(ItemBase.SignalName.PlacedDown);
			ItemHeld = null;
			return;
		}

		foreach (InventoryGrid inv in Inventories)
		{
			if (inv.GetGlobalRect().HasPoint(MousePos))
			{
				area = new Rect2(inv.HoverRect.GlobalPosition, ItemHeld.GetGlobalRect().Size);
				if (inv.AreaIsClear(area, new Godot.Collections.Array { ItemHeld }))
				{
					ItemHeld.Reparent(inv);
					ItemHeld.GlobalPosition = inv.HoverRect.GlobalPosition;
					Offset = Vector2.Zero;
					ItemHeld.EmitSignal(ItemBase.SignalName.PlacedDown);
					ItemHeld = null;
				}
			}
		}
	}

	// ------------------- Validation ------------------- //
	public bool IsAValidSpot(Rect2 area)
	{
		foreach (InventoryGrid inv in Inventories)
		{
			if (inv.GetGlobalRect().HasPoint(MousePos) || inv.IsInsideRect(area))
				return true;
		}
		return false;
	}

	public bool AreaIsClear(Rect2 zone, Godot.Collections.Array exclude)
	{
		foreach (ItemBase cell in GetItems())
		{
			if (!exclude.Contains(cell))
			{
				if (cell.GetGlobalRect().Intersects(zone))
					return false;
			}
		}
		return IsInsideRect(zone);
	}

	public bool IsInsideRect(Rect2 zone)
	{
		if (!GetGlobalRect().HasPoint(zone.Position + new Vector2(1, 1)) ||
			!GetGlobalRect().HasPoint(zone.End - new Vector2(1, 1)))
			return false;

		return true;
	}

	public bool LocationIsClear(Vector2 pos)
	{
		foreach (ItemBase cell in GetItems())
		{
			if (cell != ItemHeld)
			{
				if (cell.GetGlobalRect().HasPoint(pos))
					return false;
			}
		}
		return true;
	}

	public Godot.Collections.Array<Node> GetItems()
	{
		// skip hover rect (first child)
		return GetChildren().Slice(1, GetChildCount() - 1);
	}

	// ------------------- Save/Load Helpers ------------------- //
	public void SaveToFile(List<Dictionary> itemList, string filePath)
	{
		if (itemList.Count == 0)
		{
			GD.PrintErr("Nothing to save!");
			return;
		}

		using var file = FileAccess.Open(filePath, FileAccess.ModeFlags.Write);
		var godotArray = new Godot.Collections.Array<Dictionary>(itemList);
		file.StoreVar(godotArray);
		GD.PrintRich("[color=green]Items saved![/color]");
	}

	public List<Dictionary> LoadFromFile(string filePath)
{
	if (!FileAccess.FileExists(filePath))
	{
		GD.PrintErr("No file found!");
		return new List<Dictionary>();
	}

	var json = FileAccess.GetFileAsString(filePath);
	var data = JsonSerializer.Deserialize<List<Dictionary>>(json);
	return data ?? new List<Dictionary>();
}
}
