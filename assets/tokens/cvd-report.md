# Colour vision deficiency simulation · INTAG Digital Solutions

Roughly 1 in 12 men and 1 in 200 women have some form of color vision deficiency. The risk is not that colours look different. It is that two colours carrying *different meaning* become the same colour. Success-green against error-red is the classic failure.

Simulation uses the Brettel/Vienot transforms via coloraide filters.

## Simulated appearance

| Token | Original | Protan | Deutan | Tritan |
| --- | --- | --- | --- | --- |
| `forest.400` | `#88b5b3` | `#b1b1b3` | `#a9a9b4` | `#8cb2c2` |
| `forest.500` | `#639997` | `#949497` | `#8c8c98` | `#6896a8` |
| `forest.600` | `#407371` | `#6f6f71` | `#676772` | `#457080` |
| `forest.700` | `#386462` | `#606062` | `#5a5a63` | `#3c626f` |
| `palm.400` | `#6cbf91` | `#b8b891` | `#acac93` | `#7db6cc` |
| `palm.500` | `#329e69` | `#969669` | `#89896b` | `#4e94ab` |
| `palm.600` | `#1c8958` | `#828258` | `#76765a` | `#3d8095` |
| `palm.700` | `#066c42` | `#666642` | `#5c5c44` | `#2a6576` |
| `terracotta.400` | `#f28b6b` | `#9b9b6c` | `#b2b266` | `#f58593` |
| `terracotta.500` | `#e8704a` | `#85854b` | `#a0a042` | `#eb697c` |
| `terracotta.600` | `#bc4c27` | `#616129` | `#7b7b1b` | `#be4559` |
| `terracotta.700` | `#973817` | `#4b4b19` | `#616108` | `#993243` |
| `apricot.400` | `#d59d74` | `#a5a574` | `#b0b072` | `#d9979e` |
| `apricot.500` | `#bd7d4b` | `#86864c` | `#949447` | `#c1767f` |
| `apricot.600` | `#a06434` | `#6d6d35` | `#7a7a30` | `#a35e66` |
| `apricot.700` | `#804d23` | `#555524` | `#5f5f1f` | `#83484f` |
| `sand.400` | `#b4a8a1` | `#a9a9a1` | `#acaca1` | `#b5a7a8` |
| `sand.500` | `#90837b` | `#85857b` | `#87877b` | `#918283` |
| `sand.600` | `#7e726a` | `#73736a` | `#76766a` | `#7f7172` |
| `sand.700` | `#635852` | `#595952` | `#5b5b52` | `#645758` |
| `warning.400` | `#e29e3f` | `#a7a740` | `#b5b539` | `#e8949d` |
| `warning.500` | `#c77a00` | `#868605` | `#969600` | `#cc707c` |
| `warning.600` | `#a66300` | `#6d6d03` | `#7c7c00` | `#aa5b65` |
| `warning.700` | `#834c00` | `#545402` | `#606000` | `#86454e` |
| `error.400` | `#fa827b` | `#96967c` | `#b1b176` | `#fc7f8f` |
| `error.500` | `#e55955` | `#757556` | `#95954e` | `#e6556c` |
| `error.600` | `#cb4644` | `#626245` | `#81813c` | `#cc425a` |
| `error.700` | `#9e2c2d` | `#46462e` | `#606026` | `#9f283f` |
| `info.400` | `#7fb4c6` | `#afafc6` | `#a7a7c7` | `#7fb4c8` |
| `info.500` | `#5898ac` | `#9393ac` | `#8989ad` | `#5998ad` |
| `info.600` | `#4c8a9d` | `#85859d` | `#7c7c9e` | `#4d8a9e` |
| `info.700` | `#2d6373` | `#5f5f73` | `#575774` | `#2d6374` |

## Confusable pairs

Pairs whose simulated appearance falls within delta-E 2000 of 10 of each other. Below roughly 10 the two colors are hard to tell apart at UI scale; below 5 they are effectively identical. Cross-role hits matter most. If `success.500` and `error.500` collide, the palette needs a lightness difference or a non-colour cue: an icon, a label, a pattern. A different hue will not fix it.

| Token A | Token B | CVD type | delta-E 2000 | Severity |
| --- | --- | --- | ---: | --- |
| `terracotta.500` | `apricot.500` | protan | 0.4 | identical |
| `terracotta.700` | `warning.700` | deutan | 0.7 | identical |
| `apricot.400` | `error.400` | deutan | 0.7 | identical |
| `palm.400` | `info.400` | tritan | 0.9 | identical |
| `palm.700` | `info.700` | tritan | 1.0 | identical |
| `apricot.500` | `error.500` | deutan | 1.2 | identical |
| `apricot.700` | `error.700` | deutan | 1.2 | identical |
| `apricot.700` | `warning.700` | tritan | 1.3 | identical |
| `palm.500` | `terracotta.400` | protan | 1.7 | identical |
| `terracotta.400` | `error.400` | tritan | 1.7 | identical |
| `palm.500` | `info.500` | tritan | 1.8 | identical |
| `apricot.600` | `warning.600` | tritan | 1.8 | identical |
| `terracotta.700` | `error.700` | tritan | 1.9 | identical |
| `terracotta.600` | `warning.600` | deutan | 2.1 | identical |
| `palm.700` | `error.600` | protan | 2.5 | identical |
| `forest.700` | `info.700` | tritan | 2.6 | identical |
| `terracotta.600` | `error.600` | tritan | 2.7 | identical |
| `terracotta.400` | `apricot.400` | deutan | 2.7 | identical |
| `forest.500` | `info.500` | tritan | 2.8 | identical |
| `apricot.500` | `warning.500` | tritan | 2.8 | identical |
| `apricot.600` | `error.600` | deutan | 2.9 | identical |
| `forest.400` | `info.400` | tritan | 3.0 | identical |
| `terracotta.600` | `apricot.600` | deutan | 3.1 | identical |
| `terracotta.400` | `apricot.400` | protan | 3.1 | identical |
| `apricot.400` | `warning.400` | tritan | 3.3 | identical |
| `terracotta.700` | `apricot.700` | deutan | 3.3 | identical |
| `forest.700` | `palm.700` | tritan | 3.3 | identical |
| `terracotta.400` | `error.400` | deutan | 3.3 | identical |
| `terracotta.700` | `apricot.700` | protan | 3.4 | identical |
| `palm.500` | `info.600` | tritan | 3.5 | identical |
| `forest.400` | `palm.400` | tritan | 3.6 | identical |
| `apricot.700` | `warning.700` | deutan | 3.9 | identical |
| `forest.500` | `palm.500` | tritan | 3.9 | identical |
| `palm.600` | `terracotta.500` | protan | 3.9 | identical |
| `palm.600` | `apricot.500` | protan | 4.0 | identical |
| `palm.600` | `info.600` | tritan | 4.0 | identical |
| `terracotta.600` | `apricot.700` | protan | 4.4 | identical |
| `terracotta.700` | `error.700` | deutan | 4.4 | identical |
| `terracotta.600` | `apricot.600` | protan | 4.4 | identical |
| `terracotta.400` | `warning.400` | tritan | 4.5 | identical |
| `terracotta.500` | `error.500` | tritan | 4.5 | identical |
| `terracotta.500` | `apricot.500` | deutan | 4.5 | identical |
| `palm.500` | `apricot.400` | protan | 4.7 | identical |
| `terracotta.600` | `error.600` | deutan | 4.8 | identical |
| `terracotta.500` | `error.500` | deutan | 4.9 | identical |
| `warning.700` | `error.700` | deutan | 5.0 | identical |
| `apricot.600` | `warning.600` | deutan | 5.1 | hard to distinguish |
| `forest.600` | `palm.700` | tritan | 5.2 | hard to distinguish |
| `apricot.700` | `warning.700` | protan | 5.2 | hard to distinguish |
| `forest.600` | `info.700` | tritan | 5.4 | hard to distinguish |
| `forest.500` | `info.600` | tritan | 5.4 | hard to distinguish |
| `palm.700` | `apricot.600` | protan | 5.5 | hard to distinguish |
| `palm.400` | `sand.400` | deutan | 5.5 | hard to distinguish |
| `palm.700` | `terracotta.600` | protan | 5.5 | hard to distinguish |
| `palm.500` | `error.400` | protan | 5.6 | hard to distinguish |
| `terracotta.700` | `warning.700` | protan | 5.6 | hard to distinguish |
| `terracotta.500` | `warning.500` | tritan | 5.7 | hard to distinguish |
| `terracotta.500` | `warning.500` | deutan | 5.7 | hard to distinguish |
| `palm.600` | `error.500` | protan | 5.8 | hard to distinguish |
| `terracotta.500` | `error.400` | tritan | 5.8 | hard to distinguish |
| `forest.400` | `sand.400` | protan | 6.0 | hard to distinguish |
| `terracotta.600` | `warning.700` | protan | 6.1 | hard to distinguish |
| `palm.700` | `error.500` | protan | 6.1 | hard to distinguish |
| `warning.400` | `error.400` | tritan | 6.1 | hard to distinguish |
| `terracotta.400` | `error.400` | protan | 6.2 | hard to distinguish |
| `forest.700` | `sand.700` | protan | 6.2 | hard to distinguish |
| `terracotta.600` | `warning.600` | tritan | 6.2 | hard to distinguish |
| `palm.400` | `apricot.400` | protan | 6.2 | hard to distinguish |
| `palm.600` | `sand.600` | deutan | 6.3 | hard to distinguish |
| `terracotta.700` | `warning.700` | tritan | 6.3 | hard to distinguish |
| `forest.600` | `palm.600` | tritan | 6.4 | hard to distinguish |
| `palm.700` | `sand.700` | deutan | 6.4 | hard to distinguish |
| `warning.600` | `error.600` | deutan | 6.5 | hard to distinguish |
| `forest.600` | `sand.600` | protan | 6.5 | hard to distinguish |
| `palm.500` | `apricot.500` | protan | 6.6 | hard to distinguish |
| `terracotta.400` | `warning.400` | deutan | 6.7 | hard to distinguish |
| `apricot.600` | `warning.600` | protan | 6.7 | hard to distinguish |
| `palm.500` | `sand.500` | deutan | 6.8 | hard to distinguish |
| `apricot.500` | `error.600` | deutan | 6.8 | hard to distinguish |
| `terracotta.500` | `warning.400` | deutan | 6.9 | hard to distinguish |
| `warning.500` | `error.500` | tritan | 7.0 | hard to distinguish |
| `palm.500` | `terracotta.500` | protan | 7.0 | hard to distinguish |
| `apricot.500` | `warning.500` | deutan | 7.1 | hard to distinguish |
| `terracotta.600` | `error.600` | protan | 7.2 | hard to distinguish |
| `palm.700` | `apricot.700` | protan | 7.3 | hard to distinguish |
| `terracotta.400` | `apricot.400` | tritan | 7.4 | hard to distinguish |
| `terracotta.700` | `apricot.700` | tritan | 7.5 | hard to distinguish |
| `terracotta.700` | `error.700` | protan | 7.5 | hard to distinguish |
| `apricot.600` | `error.500` | protan | 7.6 | hard to distinguish |
| `apricot.700` | `error.600` | protan | 7.6 | hard to distinguish |
| `terracotta.500` | `apricot.400` | deutan | 7.7 | hard to distinguish |
| `terracotta.600` | `warning.600` | protan | 7.7 | hard to distinguish |
| `apricot.400` | `error.400` | protan | 7.7 | hard to distinguish |
| `terracotta.600` | `apricot.600` | tritan | 7.9 | hard to distinguish |
| `warning.600` | `error.600` | tritan | 7.9 | hard to distinguish |
| `terracotta.400` | `apricot.500` | protan | 7.9 | hard to distinguish |
| `forest.400` | `info.400` | deutan | 7.9 | hard to distinguish |
| `apricot.600` | `error.600` | protan | 8.0 | hard to distinguish |
| `warning.500` | `error.500` | deutan | 8.1 | hard to distinguish |
| `warning.700` | `error.700` | tritan | 8.2 | hard to distinguish |
| `terracotta.500` | `apricot.500` | tritan | 8.2 | hard to distinguish |
| `sand.500` | `error.400` | protan | 8.4 | hard to distinguish |
| `terracotta.500` | `error.400` | deutan | 8.4 | hard to distinguish |
| `apricot.700` | `error.700` | protan | 8.5 | hard to distinguish |
| `forest.700` | `info.700` | deutan | 8.6 | hard to distinguish |
| `sand.600` | `error.500` | protan | 8.6 | hard to distinguish |
| `apricot.400` | `error.500` | deutan | 8.7 | hard to distinguish |
| `palm.600` | `terracotta.400` | protan | 8.7 | hard to distinguish |
| `forest.500` | `sand.400` | protan | 8.8 | hard to distinguish |
| `terracotta.400` | `error.500` | deutan | 8.8 | hard to distinguish |
| `palm.600` | `info.500` | tritan | 8.8 | hard to distinguish |
| `terracotta.500` | `warning.500` | protan | 8.9 | hard to distinguish |
| `forest.500` | `info.500` | deutan | 8.9 | hard to distinguish |
| `apricot.500` | `warning.500` | protan | 8.9 | hard to distinguish |
| `palm.600` | `error.400` | protan | 8.9 | hard to distinguish |
| `terracotta.500` | `error.500` | protan | 8.9 | hard to distinguish |
| `forest.700` | `info.700` | protan | 8.9 | hard to distinguish |
| `palm.400` | `terracotta.400` | protan | 9.0 | hard to distinguish |
| `apricot.400` | `error.400` | tritan | 9.0 | hard to distinguish |
| `terracotta.400` | `warning.500` | tritan | 9.0 | hard to distinguish |
| `forest.500` | `info.400` | tritan | 9.0 | hard to distinguish |
| `palm.400` | `error.400` | deutan | 9.1 | hard to distinguish |
| `forest.500` | `sand.500` | protan | 9.2 | hard to distinguish |
| `apricot.500` | `error.500` | protan | 9.2 | hard to distinguish |
| `terracotta.400` | `apricot.500` | deutan | 9.2 | hard to distinguish |
| `palm.700` | `error.700` | deutan | 9.2 | hard to distinguish |
| `apricot.400` | `warning.400` | deutan | 9.3 | hard to distinguish |
| `forest.400` | `info.400` | protan | 9.3 | hard to distinguish |
| `apricot.700` | `error.700` | tritan | 9.3 | hard to distinguish |
| `palm.600` | `apricot.600` | protan | 9.3 | hard to distinguish |
| `forest.500` | `palm.600` | tritan | 9.3 | hard to distinguish |
| `forest.600` | `info.700` | deutan | 9.3 | hard to distinguish |
| `warning.500` | `error.400` | tritan | 9.4 | hard to distinguish |
| `terracotta.600` | `error.700` | tritan | 9.4 | hard to distinguish |
| `palm.600` | `sand.500` | deutan | 9.4 | hard to distinguish |
| `terracotta.500` | `apricot.600` | protan | 9.4 | hard to distinguish |
| `forest.700` | `sand.600` | protan | 9.5 | hard to distinguish |
| `palm.400` | `info.500` | tritan | 9.5 | hard to distinguish |
| `apricot.600` | `warning.700` | tritan | 9.5 | hard to distinguish |
| `sand.700` | `error.600` | protan | 9.5 | hard to distinguish |
| `apricot.500` | `warning.600` | tritan | 9.5 | hard to distinguish |
| `palm.500` | `sand.600` | deutan | 9.6 | hard to distinguish |
| `apricot.600` | `error.600` | tritan | 9.6 | hard to distinguish |
| `forest.500` | `palm.400` | tritan | 9.6 | hard to distinguish |
| `apricot.400` | `warning.400` | protan | 9.6 | hard to distinguish |
| `apricot.500` | `error.500` | tritan | 9.6 | hard to distinguish |
| `palm.400` | `apricot.400` | deutan | 9.6 | hard to distinguish |
| `sand.400` | `error.400` | protan | 9.6 | hard to distinguish |
| `terracotta.700` | `apricot.600` | deutan | 9.7 | hard to distinguish |
| `forest.500` | `info.500` | protan | 9.7 | hard to distinguish |
| `terracotta.600` | `apricot.500` | deutan | 9.7 | hard to distinguish |
| `terracotta.600` | `error.500` | tritan | 9.8 | hard to distinguish |
| `warning.400` | `error.400` | deutan | 9.9 | hard to distinguish |
| `apricot.500` | `error.400` | deutan | 9.9 | hard to distinguish |
| `forest.600` | `info.600` | tritan | 9.9 | hard to distinguish |
| `forest.500` | `info.600` | deutan | 9.9 | hard to distinguish |
| `apricot.600` | `error.500` | deutan | 9.9 | hard to distinguish |
| `apricot.600` | `warning.700` | protan | 10.0 | hard to distinguish |

## What to do about a collision

1. Separate the two colors in **lightness**, not hue. Lightness survives every CVD type; hue does not.
2. Add a redundant cue: icon shape, text label, pattern, position.
3. Re-run this check after the fix rather than assuming it worked.

