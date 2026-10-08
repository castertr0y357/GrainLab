import ast
import os
import re

engines_dir = 'e:/Coding Projects/GrainLab/apps/core/engines'

ARCHETYPE_TARGETS = {
    'BoiledBagelArchetype': {'target_hydration_ratio': 55.0, 'target_fat_ratio': 2.0, 'target_sugar_ratio': 5.0, 'target_protein_pct': 14.0, 'base_leavening_ratio': 1.0},
    'TwistedPretzelArchetype': {'target_hydration_ratio': 50.0, 'target_fat_ratio': 5.0, 'target_sugar_ratio': 0.0, 'target_protein_pct': 12.0, 'base_leavening_ratio': 1.0},
    'SpongeCakeArchetype': {'target_hydration_ratio': 100.0, 'target_fat_ratio': 20.0, 'target_sugar_ratio': 100.0, 'target_protein_pct': 9.0, 'base_leavening_ratio': 2.0},
    'CreamedCakeArchetype': {'target_hydration_ratio': 80.0, 'target_fat_ratio': 50.0, 'target_sugar_ratio': 100.0, 'target_protein_pct': 9.0, 'base_leavening_ratio': 2.0},
    'PoundCakeArchetype': {'target_hydration_ratio': 50.0, 'target_fat_ratio': 100.0, 'target_sugar_ratio': 100.0, 'target_protein_pct': 9.0, 'base_leavening_ratio': 1.5},
    'GriddleBatterArchetype': {'target_hydration_ratio': 120.0, 'target_fat_ratio': 15.0, 'target_sugar_ratio': 10.0, 'target_protein_pct': 9.0, 'base_leavening_ratio': 3.0},
    'PipedShellArchetype': {'target_hydration_ratio': 150.0, 'target_fat_ratio': 80.0, 'target_sugar_ratio': 0.0, 'target_protein_pct': 11.0, 'base_leavening_ratio': 0.0},
    'ExtrusionFriedPasteArchetype': {'target_hydration_ratio': 150.0, 'target_fat_ratio': 40.0, 'target_sugar_ratio': 10.0, 'target_protein_pct': 11.0, 'base_leavening_ratio': 0.0},
    'SavoryEmulsionArchetype': {'target_hydration_ratio': 150.0, 'target_fat_ratio': 80.0, 'target_sugar_ratio': 0.0, 'target_protein_pct': 11.0, 'base_leavening_ratio': 0.0},
    'DropCookieArchetype': {'target_hydration_ratio': 15.0, 'target_fat_ratio': 70.0, 'target_sugar_ratio': 90.0, 'target_protein_pct': 10.0, 'base_leavening_ratio': 1.5},
    'BarCookieArchetype': {'target_hydration_ratio': 20.0, 'target_fat_ratio': 60.0, 'target_sugar_ratio': 100.0, 'target_protein_pct': 10.0, 'base_leavening_ratio': 1.0},
    'SliceBakeArchetype': {'target_hydration_ratio': 10.0, 'target_fat_ratio': 80.0, 'target_sugar_ratio': 60.0, 'target_protein_pct': 10.0, 'base_leavening_ratio': 0.5},
    'RolledCutoutArchetype': {'target_hydration_ratio': 10.0, 'target_fat_ratio': 50.0, 'target_sugar_ratio': 50.0, 'target_protein_pct': 10.0, 'base_leavening_ratio': 0.5},
    'LeavenedFlatbreadArchetype': {'target_hydration_ratio': 65.0, 'target_fat_ratio': 10.0, 'target_sugar_ratio': 2.0, 'target_protein_pct': 11.0, 'base_leavening_ratio': 1.5},
    'UnleavenedStretchedArchetype': {'target_hydration_ratio': 60.0, 'target_fat_ratio': 15.0, 'target_sugar_ratio': 0.0, 'target_protein_pct': 11.0, 'base_leavening_ratio': 0.0},
    'BlisteredGriddleArchetype': {'target_hydration_ratio': 70.0, 'target_fat_ratio': 5.0, 'target_sugar_ratio': 0.0, 'target_protein_pct': 11.0, 'base_leavening_ratio': 1.5},
    'CrispFlatbreadArchetype': {'target_hydration_ratio': 45.0, 'target_fat_ratio': 20.0, 'target_sugar_ratio': 0.0, 'target_protein_pct': 11.0, 'base_leavening_ratio': 0.0},
    'YeastRaisedDonutArchetype': {'target_hydration_ratio': 50.0, 'target_fat_ratio': 15.0, 'target_sugar_ratio': 15.0, 'target_protein_pct': 12.0, 'base_leavening_ratio': 2.0},
    'CakeDonutArchetype': {'target_hydration_ratio': 65.0, 'target_fat_ratio': 20.0, 'target_sugar_ratio': 40.0, 'target_protein_pct': 9.0, 'base_leavening_ratio': 3.0},
    'FritterBeignetArchetype': {'target_hydration_ratio': 80.0, 'target_fat_ratio': 10.0, 'target_sugar_ratio': 10.0, 'target_protein_pct': 10.0, 'base_leavening_ratio': 2.0},
    'FriedLaminateArchetype': {'target_hydration_ratio': 40.0, 'target_fat_ratio': 50.0, 'target_sugar_ratio': 10.0, 'target_protein_pct': 12.0, 'base_leavening_ratio': 1.5},
    'HearthBouleArchetype': {'target_hydration_ratio': 75.0, 'target_fat_ratio': 0.0, 'target_sugar_ratio': 0.0, 'target_protein_pct': 12.0, 'base_leavening_ratio': 1.5},
    'HighHydrationSlabArchetype': {'target_hydration_ratio': 85.0, 'target_fat_ratio': 5.0, 'target_sugar_ratio': 0.0, 'target_protein_pct': 12.0, 'base_leavening_ratio': 1.5},
    'TaperedBaguetteArchetype': {'target_hydration_ratio': 70.0, 'target_fat_ratio': 0.0, 'target_sugar_ratio': 0.0, 'target_protein_pct': 12.0, 'base_leavening_ratio': 1.5},
    'FlashPizzaArchetype': {'target_hydration_ratio': 65.0, 'target_fat_ratio': 5.0, 'target_sugar_ratio': 0.0, 'target_protein_pct': 12.0, 'base_leavening_ratio': 1.0},
    'SandwichPanArchetype': {'target_hydration_ratio': 65.0, 'target_fat_ratio': 10.0, 'target_sugar_ratio': 5.0, 'target_protein_pct': 12.0, 'base_leavening_ratio': 2.0},
    'FreeformBraidedArchetype': {'target_hydration_ratio': 55.0, 'target_fat_ratio': 20.0, 'target_sugar_ratio': 15.0, 'target_protein_pct': 12.0, 'base_leavening_ratio': 2.0},
    'SoftDinnerRollArchetype': {'target_hydration_ratio': 60.0, 'target_fat_ratio': 25.0, 'target_sugar_ratio': 20.0, 'target_protein_pct': 11.0, 'base_leavening_ratio': 2.0},
    'FilledSweetRollArchetype': {'target_hydration_ratio': 50.0, 'target_fat_ratio': 30.0, 'target_sugar_ratio': 25.0, 'target_protein_pct': 11.0, 'base_leavening_ratio': 2.0},
    'SheetedRibbonArchetype': {'target_hydration_ratio': 45.0, 'target_fat_ratio': 0.0, 'target_sugar_ratio': 0.0, 'target_protein_pct': 11.0, 'base_leavening_ratio': 0.0},
    'StuffedPocketArchetype': {'target_hydration_ratio': 50.0, 'target_fat_ratio': 5.0, 'target_sugar_ratio': 0.0, 'target_protein_pct': 11.0, 'base_leavening_ratio': 0.0},
    'ExtrudedShapeArchetype': {'target_hydration_ratio': 35.0, 'target_fat_ratio': 0.0, 'target_sugar_ratio': 0.0, 'target_protein_pct': 13.0, 'base_leavening_ratio': 0.0},
    'AlkalineNoodlesArchetype': {'target_hydration_ratio': 40.0, 'target_fat_ratio': 0.0, 'target_sugar_ratio': 0.0, 'target_protein_pct': 12.0, 'base_leavening_ratio': 0.0},
    'LayeredViennoiserieArchetype': {'target_hydration_ratio': 45.0, 'target_fat_ratio': 50.0, 'target_sugar_ratio': 10.0, 'target_protein_pct': 12.0, 'base_leavening_ratio': 1.5},
    'InvertedPuffArchetype': {'target_hydration_ratio': 45.0, 'target_fat_ratio': 80.0, 'target_sugar_ratio': 0.0, 'target_protein_pct': 11.0, 'base_leavening_ratio': 0.0},
    'ShortcrustTartArchetype': {'target_hydration_ratio': 30.0, 'target_fat_ratio': 60.0, 'target_sugar_ratio': 10.0, 'target_protein_pct': 9.0, 'base_leavening_ratio': 0.0},
    'PaperThinPhylloArchetype': {'target_hydration_ratio': 50.0, 'target_fat_ratio': 10.0, 'target_sugar_ratio': 0.0, 'target_protein_pct': 12.0, 'base_leavening_ratio': 0.0},
    'ChemicalLoafArchetype': {'target_hydration_ratio': 80.0, 'target_fat_ratio': 30.0, 'target_sugar_ratio': 40.0, 'target_protein_pct': 9.0, 'base_leavening_ratio': 3.0},
    'LayeredSconeArchetype': {'target_hydration_ratio': 60.0, 'target_fat_ratio': 40.0, 'target_sugar_ratio': 20.0, 'target_protein_pct': 9.0, 'base_leavening_ratio': 4.0},
    'DroppedBiscuitArchetype': {'target_hydration_ratio': 70.0, 'target_fat_ratio': 40.0, 'target_sugar_ratio': 5.0, 'target_protein_pct': 9.0, 'base_leavening_ratio': 4.0},
    'TexturedMuffinArchetype': {'target_hydration_ratio': 90.0, 'target_fat_ratio': 30.0, 'target_sugar_ratio': 45.0, 'target_protein_pct': 9.0, 'base_leavening_ratio': 3.5},
}

for f in os.listdir(engines_dir):
    if not f.endswith('_engine.py') or f == 'base_engine.py':
        continue
    p = os.path.join(engines_dir, f)
    with open(p, encoding='utf-8') as file:
        content = file.read()

    lines = content.split('\n')
    tree = ast.parse(content)
    
    insertions = []
    
    # Track changes to make
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name in ARCHETYPE_TARGETS:
            targets = ARCHETYPE_TARGETS[node.name]
            block = []
            for k, v in targets.items():
                block.append(f"    {k} = {v}")
            # Insert after the class definition line
            insertions.append((node.lineno, '\n'.join(block)))
            
    # Apply insertions in reverse order to not mess up line numbers
    for lineno, text in sorted(insertions, reverse=True):
        lines.insert(lineno, text)
        
    with open(p, 'w', encoding='utf-8') as file:
        file.write('\n'.join(lines))
