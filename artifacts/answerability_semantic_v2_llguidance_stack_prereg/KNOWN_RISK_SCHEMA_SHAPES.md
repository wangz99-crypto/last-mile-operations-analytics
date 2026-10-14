# Frozen risk shapes

Schema identity is fixed in PREREGISTERED_STACK.json. These are pointers into the original file, not rewritten substitute schemas.

- /oneOf/0/properties/material_asks
- /oneOf/1/properties/material_asks
- /properties/material_asks/items
- /properties/material_asks/items/allOf/0

The first two preserve LMFE's primary untyped oneOf/material_asks failure shape. The item subtree and its conditional allOf preserve the independent additional incompatibility. Future K3 must extract unchanged subtrees, record identity, and compile/validate without relaxation before tokenizer/matcher/model activity. No subtree execution occurred here.

Static llguidance 1.9.1 blockers additionally occur at:

- /properties/material_asks/items/properties/supporting_evidence_ranks/uniqueItems
- /properties/material_asks/items/allOf/0/if
- /properties/material_asks/items/allOf/0/then
- /properties/material_asks/items/allOf/0/else
- /oneOf/1/properties/material_asks/contains
- /oneOf/2/anyOf/1/properties/material_asks/contains

All are CRITICAL: omitting them admits objects that the frozen raw schema rejects before adapter processing. This source finding blocks progression now; it does not constitute a measured matcher result.
