using Godot;
using System;
using System.Collections.Generic;

public partial class ItemBase : TextureRect
{
	// ------------------- Fields ------------------- //
	private InventoryGrid gridMap;
	private MenuButton actionList;
	private ColorRect gridSpace;
	private Label countLabel;
	private ColorRect shadow;

	private Vector2 curSize = Vector2.Zero;
	private bool isRotated = false;
	private bool stackable = false;
	private ItemData itemData;
	private int quantity = 1;

	private Vector2 lastPosition = Vector2.Zero;
	private List<Node> inventories = new();

	private static readonly Color ValidSpot = new Color(0.45f, 1f, 0f, 0.3f);
	private static readonly Color OccupiedSpot = new Color(1f, 0f, 0f, 0.3f);
	private static readonly Color SwitchSpot = new Color(1f, 0.68f, 0f, 0.3f);

	// ------------------- Properties ------------------- //
	public ItemData ItemData => itemData;
	public bool Stackable => stackable;
	public int Quantity
	{
		get => quantity;
		set => quantity = value;
	}
	public bool IsRotated => isRotated;

	// ------------------- Signals ------------------- //
    [Signal] public delegate void PickedUpEventHandler(ItemBase item);
    [Signal] public delegate void PlacedDownEventHandler(ItemBase item);
    public InventoryGrid Grid_Map;


    public override void _Ready()
    {
        Grid_Map = GetParent<InventoryGrid>();
    }

    public void PrepItem(ItemData itemData)
    {
        curSize = itemData.GridSize * Grid_Map.CellSize;
    }

    public void Rotate()
    {
        
    }
}
