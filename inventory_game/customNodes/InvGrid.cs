using Godot;
using System;
using Godot.Collections;
using System.Collections.Generic;

[GlobalClass]
public partial class InvGrid : TextureRect
{
    [ExportCategory("Grid")]
    [Export] public int CellSize { get; set; } = 40;
    [Export(PropertyHint.Range, "1,9999,1")] public int GridH { get; set; } = 8;
    [Export(PropertyHint.Range, "1,9999,1")] public int GridW { get; set; } = 8;
    [Export] public Texture2D HoverTxtr { get; set; }
    [Export] public Texture2D Txtr { get; set; }


    public TextureRect HoverRect { get; private set; }
    public Vector2 MousePos { get; set; } = Vector2.Zero;

    public override void _Ready()
    {
        GlobalPosition = Vector2.Zero;
        StretchMode = StretchModeEnum.Tile;
        CustomMinimumSize = new Vector2I(CellSize * GridW, CellSize * GridH);

        var hoverChild = new TextureRect
        {
            Texture = HoverTxtr,
            Size = new Vector2I(CellSize, CellSize)
        };
        AddChild(hoverChild);
        HoverRect = hoverChild;
    }

    public override void _Process(double delta)
    {
        StretchMode = StretchModeEnum.Tile;
        CustomMinimumSize = new Vector2I(CellSize * GridW, CellSize * GridH);
        MousePos = GetGlobalMousePosition();
        HoverMouse();
    }

    //Hover
    private void HoverMouse()
    {
        if (GetGlobalRect().HasPoint(MousePos))
        {  
            Vector2 currPos = Vector2.Zero;
            Vector2 prevPos = Vector2.Zero;
            Vector2 snappedPos;

            snappedPos = (MousePos - GlobalPosition) - (new Vector2(CellSize, CellSize) / 2);
            HoverRect.GlobalPosition = snappedPos.Snapped(new Vector2(CellSize, CellSize));
            HoverRect.GlobalPosition = HoverRect.GlobalPosition.Clamp
                (
                    Vector2.Zero, new Vector2(Size.Y - CellSize, Size.X - CellSize)
                );
        }
    }
}
