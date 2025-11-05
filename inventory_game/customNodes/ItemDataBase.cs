using Godot;
using System;
using System.Collections.Generic;

[GlobalClass]
public partial class ItemDataBase : Node
{
    [Export] public Godot.Collections.Array<ItemData> Items { get; set; } = new();
}
