using Godot;
using System;

[GlobalClass]
public partial class ItemData : Node
{
    [Export]
    public string Name { get; set; } = "";

    [Export]
    public CompressedTexture2D Icon { get; set; }

    [Export]
    public Vector2I GridSize { get; set; } = Vector2I.One;

    [Export]
    public bool Stackable { get; set; } = false;
}
