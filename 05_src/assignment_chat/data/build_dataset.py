# Generates data/animal_facts.csv, the knowledge base for Service 2.
#
# Hand-typed instead of scraped, so it stays small, license-clean, and
# doesn't need internet access to build. Conservation statuses are
# simplified for this project, not pulled from the real IUCN Red List.
#
# Each row's "description" column is what actually gets embedded in
# Chroma (see services/semantic_search.py).
#
# Run: python data/build_dataset.py

import csv
import os

# (name, scientific_name, category, habitat, region, diet, conservation_status, fun_fact)
ANIMALS = [
    # --- Mammals ---
    ("Lion", "Panthera leo", "Mammal", "open savanna and grassland", "sub-Saharan Africa", "large herbivores such as zebra and wildebeest (carnivore)", "Vulnerable", "The only big cat that lives in social groups, called prides."),
    ("Tiger", "Panthera tigris", "Mammal", "forests, mangroves, and grasslands", "South and Southeast Asia, Russian Far East", "deer, wild boar, and other large mammals (carnivore)", "Endangered", "Each tiger has a unique stripe pattern, like a fingerprint."),
    ("African Elephant", "Loxodonta africana", "Mammal", "savanna, forest, and desert", "sub-Saharan Africa", "grasses, bark, roots, and fruit (herbivore)", "Endangered", "The largest living land animal; a trunk has over 40,000 muscles."),
    ("Asian Elephant", "Elephas maximus", "Mammal", "tropical forest and grassland", "South and Southeast Asia", "grasses, bark, and fruit (herbivore)", "Endangered", "Smaller ears than its African cousin and only some males grow tusks."),
    ("Giraffe", "Giraffa camelopardalis", "Mammal", "savanna and open woodland", "sub-Saharan Africa", "acacia leaves and shoots (herbivore)", "Vulnerable", "The tallest living land animal, with a neck too short to have extra vertebrae - it has the same seven neck bones as a human."),
    ("Plains Zebra", "Equus quagga", "Mammal", "grassland and savanna", "eastern and southern Africa", "grasses (herbivore)", "Near Threatened", "No two zebras have the exact same stripe pattern."),
    ("Hippopotamus", "Hippopotamus amphibius", "Mammal", "rivers and lakes", "sub-Saharan Africa", "grasses (herbivore)", "Vulnerable", "Despite its bulk, a hippo can outrun a human on land over short distances."),
    ("White Rhinoceros", "Ceratotherium simum", "Mammal", "grassland and savanna", "southern Africa", "grasses (herbivore)", "Near Threatened", "The wide, square lip is built for grazing on grass, unlike the black rhino's pointed lip."),
    ("Black Rhinoceros", "Diceros bicornis", "Mammal", "savanna and shrubland", "eastern and southern Africa", "leaves and shrubs (browser/herbivore)", "Critically Endangered", "Uses its hooked upper lip to strip leaves from bushes."),
    ("Western Lowland Gorilla", "Gorilla gorilla gorilla", "Mammal", "tropical rainforest", "Central Africa", "fruit, leaves, and stems (herbivore)", "Critically Endangered", "Shares about 98% of its DNA with humans."),
    ("Chimpanzee", "Pan troglodytes", "Mammal", "tropical forest and savanna woodland", "Central and West Africa", "fruit, leaves, and insects (omnivore)", "Endangered", "Known to use tools, such as stripped twigs to fish for termites."),
    ("Bornean Orangutan", "Pongo pygmaeus", "Mammal", "tropical rainforest", "Borneo", "fruit, bark, and leaves (omnivore)", "Critically Endangered", "Spends most of its life in trees and builds a fresh sleeping nest every night."),
    ("Red Kangaroo", "Osphranter rufus", "Mammal", "arid plains and open woodland", "Australia", "grasses and shrubs (herbivore)", "Least Concern", "Can cover over 8 meters in a single hop."),
    ("Koala", "Phascolarctos cinereus", "Mammal", "eucalyptus forest", "eastern Australia", "eucalyptus leaves (herbivore)", "Vulnerable", "Sleeps up to 20 hours a day to conserve energy from its low-nutrient diet."),
    ("Giant Panda", "Ailuropoda melanoleuca", "Mammal", "temperate bamboo forest", "central China", "bamboo, almost exclusively (herbivore)", "Vulnerable", "Eats up to 40 kg of bamboo a day despite having a carnivore's digestive system."),
    ("Red Panda", "Ailurus fulgens", "Mammal", "temperate forest with bamboo understory", "Himalayas and southwestern China", "bamboo, fruit, and insects (omnivore)", "Endangered", "Not closely related to the giant panda; it's the only living member of its own family."),
    ("Polar Bear", "Ursus maritimus", "Mammal", "arctic sea ice and coastline", "the Arctic", "seals (carnivore)", "Vulnerable", "Black skin under a translucent, hollow-haired coat helps absorb heat from the sun."),
    ("Grizzly Bear", "Ursus arctos horribilis", "Mammal", "forest, mountain, and tundra", "North America", "berries, roots, fish, and small mammals (omnivore)", "Least Concern", "Has a distinctive shoulder hump made of muscle for digging."),
    ("Gray Wolf", "Canis lupus", "Mammal", "forest, tundra, and grassland", "North America, Europe, and Asia", "deer, elk, and other large prey (carnivore)", "Least Concern", "Lives and hunts in family groups called packs, led by a breeding pair."),
    ("Red Fox", "Vulpes vulpes", "Mammal", "forest, grassland, and urban edges", "widespread across the Northern Hemisphere", "small mammals, birds, and fruit (omnivore)", "Least Concern", "The most widely distributed wild carnivore on Earth."),
    ("Fennec Fox", "Vulpes zerda", "Mammal", "sandy desert", "North Africa and the Sahara", "insects, small rodents, and plants (omnivore)", "Least Concern", "Its oversized ears radiate heat and help it hear prey underground."),
    ("Meerkat", "Suricata suricatta", "Mammal", "arid grassland and desert", "southern Africa", "insects and small reptiles (omnivore)", "Least Concern", "Lives in tight-knit mobs and posts sentries to watch for predators."),
    ("Spotted Hyena", "Crocuta crocuta", "Mammal", "savanna and grassland", "sub-Saharan Africa", "large mammals, hunted or scavenged (carnivore)", "Least Concern", "Has one of the strongest bites in the animal kingdom, able to crack bone."),
    ("Cheetah", "Acinonyx jubatus", "Mammal", "open savanna and grassland", "sub-Saharan Africa", "small to medium antelope (carnivore)", "Vulnerable", "The fastest land animal, capable of short bursts near 100 km/h."),
    ("Leopard", "Panthera pardus", "Mammal", "forest, savanna, and mountains", "Africa and Asia", "a wide variety of prey (carnivore)", "Vulnerable", "Often hauls its kills up into trees to keep them from other predators."),
    ("Jaguar", "Panthera onca", "Mammal", "tropical rainforest and wetland", "Central and South America", "capybara, caiman, and fish (carnivore)", "Near Threatened", "Has the strongest bite force relative to size of any big cat."),
    ("Ocelot", "Leopardus pardalis", "Mammal", "dense forest and scrubland", "Central and South America", "small mammals and birds (carnivore)", "Least Concern", "A skilled climber and swimmer, mostly active at night."),
    ("River Otter", "Lontra canadensis", "Mammal", "rivers, lakes, and coastlines", "North America", "fish and crustaceans (carnivore)", "Least Concern", "Known for sliding down muddy or snowy banks, seemingly for play."),
    ("American Beaver", "Castor canadensis", "Mammal", "rivers, streams, and wetlands", "North America", "bark, twigs, and aquatic plants (herbivore)", "Least Concern", "Builds dams and lodges that can reshape entire wetland ecosystems."),
    ("Raccoon", "Procyon lotor", "Mammal", "forest, wetland, and urban areas", "North America", "fruit, insects, and small animals (omnivore)", "Least Concern", "Has highly sensitive front paws it uses to examine food and objects."),
    ("Striped Skunk", "Mephitis mephitis", "Mammal", "woodland, grassland, and suburbs", "North America", "insects, small rodents, and plants (omnivore)", "Least Concern", "Defends itself with a strong-smelling spray from glands near its tail."),
    ("Nine-banded Armadillo", "Dasypus novemcinctus", "Mammal", "grassland, forest, and scrub", "the Americas", "insects, especially ants and termites (insectivore)", "Least Concern", "Almost always gives birth to identical quadruplets."),
    ("Giant Anteater", "Myrmecophaga tridactyla", "Mammal", "grassland and open forest", "Central and South America", "ants and termites (insectivore)", "Vulnerable", "Its tongue can flick in and out up to 150 times a minute."),
    ("Three-toed Sloth", "Bradypus variegatus", "Mammal", "tropical rainforest canopy", "Central and South America", "leaves (herbivore)", "Least Concern", "Moves so slowly that algae often grows in its fur."),
    ("Capybara", "Hydrochoerus hydrochaeris", "Mammal", "wetland, riverbank, and grassland", "South America", "grasses and aquatic plants (herbivore)", "Least Concern", "The world's largest living rodent, and a strong swimmer."),
    ("Bactrian Camel", "Camelus bactrianus", "Mammal", "cold desert and steppe", "Central Asia", "tough desert vegetation (herbivore)", "Endangered", "Its two humps store fat, not water, for long treks between food sources."),
    ("Llama", "Lama glama", "Mammal", "high-altitude grassland", "the Andes mountains", "grasses (herbivore)", "Least Concern", "Domesticated for thousands of years as a pack animal and wool source."),
    ("Alpaca", "Vicugna pacos", "Mammal", "high-altitude grassland", "the Andes mountains", "grasses (herbivore)", "Least Concern", "Bred mainly for its soft, warm fleece rather than as a pack animal."),
    ("American Bison", "Bison bison", "Mammal", "prairie and grassland", "North America", "grasses (herbivore)", "Near Threatened", "Once nearly extinct, but conservation efforts have rebuilt herds across the continent."),
    ("Moose", "Alces alces", "Mammal", "boreal forest and wetland", "North America, Europe, and Asia", "leaves, bark, and aquatic plants (herbivore)", "Least Concern", "The largest living species of deer."),
    ("Reindeer", "Rangifer tarandus", "Mammal", "tundra and boreal forest", "the Arctic and sub-Arctic", "lichen, grasses, and leaves (herbivore)", "Vulnerable", "The only deer species where both males and females grow antlers."),
    ("Hedgehog", "Erinaceus europaeus", "Mammal", "woodland, grassland, and gardens", "Europe", "insects, worms, and small invertebrates (insectivore)", "Least Concern", "Rolls into a tight, spiny ball when threatened."),
    ("Platypus", "Ornithorhynchus anatinus", "Mammal", "rivers and streams", "eastern Australia", "insect larvae, shrimp, and worms (carnivore)", "Near Threatened", "One of the only mammals that lays eggs, and males have a venomous spur."),
    ("Short-beaked Echidna", "Tachyglossus aculeatus", "Mammal", "forest, scrubland, and desert", "Australia and New Guinea", "ants and termites (insectivore)", "Least Concern", "Along with the platypus, one of the only egg-laying mammals on Earth."),
    ("Common Wombat", "Vombatus ursinus", "Mammal", "forest and grassland", "southeastern Australia", "grasses and roots (herbivore)", "Least Concern", "Produces cube-shaped droppings, which help mark territory without rolling away."),
    ("Tasmanian Devil", "Sarcophilus harrisii", "Mammal", "forest and coastal scrubland", "Tasmania, Australia", "carrion and small animals (carnivore/scavenger)", "Endangered", "The largest carnivorous marsupial alive today, known for its powerful bite."),
    ("Warthog", "Phacochoerus africanus", "Mammal", "savanna and grassland", "sub-Saharan Africa", "grasses and roots (herbivore)", "Least Concern", "Often backs into burrows so its tusks face outward toward danger."),
    ("Okapi", "Okapia johnstoni", "Mammal", "dense tropical rainforest", "Democratic Republic of the Congo", "leaves and shoots (herbivore)", "Endangered", "Striped legs resemble a zebra, but it's actually the giraffe's closest living relative."),
    ("Aardvark", "Orycteropus afer", "Mammal", "savanna and grassland", "sub-Saharan Africa", "ants and termites (insectivore)", "Least Concern", "Digs burrows so efficiently it can disappear into the ground in minutes."),
    ("Pangolin", "Manis species", "Mammal", "forest and savanna", "Africa and Asia", "ants and termites (insectivore)", "Critically Endangered", "The only mammal covered in protective keratin scales."),
    # --- Birds ---
    ("Emperor Penguin", "Aptenodytes forsteri", "Bird", "sea ice and open ocean", "Antarctica", "fish, squid, and krill (carnivore)", "Near Threatened", "The largest penguin species; males incubate the egg on their feet through the Antarctic winter."),
    ("King Penguin", "Aptenodytes patagonicus", "Bird", "sub-Antarctic islands and ocean", "southern Atlantic and Indian Oceans", "fish and squid (carnivore)", "Least Concern", "The second-largest penguin species, with a distinctive orange neck patch."),
    ("Humboldt Penguin", "Spheniscus humboldti", "Bird", "rocky coastline", "coasts of Chile and Peru", "fish, especially anchovies (carnivore)", "Vulnerable", "One of the warm-climate penguin species, found far from Antarctica."),
    ("Bald Eagle", "Haliaeetus leucocephalus", "Bird", "lakes, rivers, and coastlines", "North America", "fish and small mammals (carnivore)", "Least Concern", "Builds some of the largest tree nests of any bird, reused and expanded yearly."),
    ("Golden Eagle", "Aquila chrysaetos", "Bird", "mountains and open country", "Northern Hemisphere", "rabbits and other small mammals (carnivore)", "Least Concern", "One of the fastest diving birds, reaching speeds over 240 km/h in a stoop."),
    ("Snowy Owl", "Bubo scandiacus", "Bird", "arctic tundra", "the Arctic", "lemmings and other small mammals (carnivore)", "Vulnerable", "Unlike most owls, it often hunts during daylight in the Arctic summer."),
    ("Great Horned Owl", "Bubo virginianus", "Bird", "forest, desert, and urban edges", "the Americas", "small mammals and birds (carnivore)", "Least Concern", "Silent flight feathers let it approach prey almost without a sound."),
    ("Scarlet Macaw", "Ara macao", "Bird", "tropical rainforest", "Central and South America", "fruit, nuts, and seeds (herbivore)", "Least Concern", "Can live 50 years or more and often mates for life."),
    ("African Grey Parrot", "Psittacus erithacus", "Bird", "tropical rainforest", "West and Central Africa", "fruit, seeds, and nuts (herbivore)", "Endangered", "Considered one of the most vocally talented and cognitively advanced parrots."),
    ("Toco Toucan", "Ramphastos toco", "Bird", "tropical forest and savanna", "South America", "fruit and small animals (omnivore)", "Least Concern", "Its oversized bill helps regulate body temperature by releasing heat."),
    ("Greater Flamingo", "Phoenicopterus roseus", "Bird", "shallow lakes and lagoons", "Africa, southern Europe, and Asia", "algae and small crustaceans (omnivore/filter feeder)", "Least Concern", "Its pink color comes from pigments in the algae and shrimp it eats."),
    ("Common Ostrich", "Struthio camelus", "Bird", "savanna and desert", "Africa", "plants, seeds, and small animals (omnivore)", "Least Concern", "The largest living bird; it cannot fly but can sprint over 70 km/h."),
    ("Emu", "Dromaius novaehollandiae", "Bird", "grassland and open woodland", "Australia", "plants, seeds, and insects (omnivore)", "Least Concern", "The second-largest living bird by height, after the ostrich."),
    ("Southern Cassowary", "Casuarius casuarius", "Bird", "tropical rainforest", "Australia and New Guinea", "fallen fruit (frugivore)", "Least Concern", "A bony helmet-like casque tops its head; considered one of the more dangerous birds."),
    ("Indian Peafowl", "Pavo cristatus", "Bird", "forest edge and farmland", "the Indian subcontinent", "seeds, insects, and small reptiles (omnivore)", "Least Concern", "Males, called peacocks, fan out iridescent tail feathers to attract mates."),
    ("American White Pelican", "Pelecanus erythrorhynchos", "Bird", "lakes and wetlands", "North America", "fish (carnivore)", "Least Concern", "Often fishes cooperatively, herding fish into shallow water with other pelicans."),
    ("Whooping Crane", "Grus americana", "Bird", "wetland and prairie marsh", "North America", "fish, insects, and plants (omnivore)", "Endangered", "One of the rarest birds in North America; conservation programs use costume-clad handlers to teach chicks migration routes."),
    ("Trumpeter Swan", "Cygnus buccinator", "Bird", "lakes, rivers, and wetlands", "North America", "aquatic plants (herbivore)", "Least Concern", "The heaviest native waterfowl in North America."),
    ("Rufous Hummingbird", "Selasphorus rufus", "Bird", "forest edge and gardens", "western North America", "nectar and small insects (nectarivore)", "Near Threatened", "Makes one of the longest migratory journeys relative to body size of any bird."),
    ("Brown Kiwi", "Apteryx mantelli", "Bird", "forest floor", "New Zealand", "insects, worms, and seeds (omnivore)", "Vulnerable", "A flightless bird with nostrils at the tip of its beak, used to sniff out food underground."),
    # --- Reptiles ---
    ("American Alligator", "Alligator mississippiensis", "Reptile", "freshwater swamp, marsh, and river", "southeastern United States", "fish, birds, and mammals (carnivore)", "Least Concern", "A conservation success story, recovering from near extinction in the mid-20th century."),
    ("Saltwater Crocodile", "Crocodylus porosus", "Reptile", "coastal wetland and river estuary", "Southeast Asia and northern Australia", "fish, birds, and mammals (carnivore)", "Least Concern", "The largest living reptile, with adult males exceeding 6 meters."),
    ("Komodo Dragon", "Varanus komodoensis", "Reptile", "dry savanna and forest", "the Indonesian islands of Komodo and Flores", "deer, pigs, and carrion (carnivore)", "Endangered", "The largest living lizard, with a bite that delivers venom and bacteria-laden saliva."),
    ("Green Iguana", "Iguana iguana", "Reptile", "tropical rainforest canopy", "Central and South America", "leaves, flowers, and fruit (herbivore)", "Least Concern", "Can drop its tail to escape a predator, then regrow it over time."),
    ("Veiled Chameleon", "Chamaeleo calyptratus", "Reptile", "mountain valleys and plateaus", "Yemen and Saudi Arabia", "insects and some plant matter (omnivore)", "Least Concern", "Its independently swiveling eyes give it a nearly 360-degree field of view."),
    ("Leopard Gecko", "Eublepharis macularius", "Reptile", "rocky, arid grassland", "South Asia and the Middle East", "insects (insectivore)", "Least Concern", "Unlike most geckos, it has movable eyelids and no adhesive toe pads."),
    ("Nile Monitor", "Varanus niloticus", "Reptile", "rivers, lakes, and wetlands", "sub-Saharan Africa", "eggs, fish, and small animals (carnivore)", "Least Concern", "One of Africa's largest lizards and a strong swimmer."),
    ("Galapagos Tortoise", "Chelonoidis niger", "Reptile", "volcanic scrubland and grassland", "the Galapagos Islands", "grasses, cactus, and fruit (herbivore)", "Vulnerable", "Among the longest-lived vertebrates, with some individuals surpassing 100 years."),
    ("Green Sea Turtle", "Chelonia mydas", "Reptile", "coastal waters, seagrass beds, and coral reefs", "tropical and subtropical oceans worldwide", "seagrass and algae as adults (herbivore)", "Endangered", "Named for the greenish color of its fat, not its shell."),
    ("Ball Python", "Python regius", "Reptile", "grassland and open forest", "West and Central Africa", "small mammals (carnivore)", "Least Concern", "Named for its habit of curling into a tight ball when threatened."),
    ("Boa Constrictor", "Boa constrictor", "Reptile", "tropical forest and scrubland", "Central and South America", "birds and mammals (carnivore)", "Least Concern", "Kills prey by constriction rather than venom, subduing it before swallowing whole."),
    ("King Cobra", "Ophiophagus hannah", "Reptile", "forest and dense jungle", "South and Southeast Asia", "primarily other snakes (carnivore)", "Vulnerable", "The world's longest venomous snake, sometimes exceeding 5 meters."),
    ("Eastern Diamondback Rattlesnake", "Crotalus adamanteus", "Reptile", "pine forest and scrubland", "southeastern United States", "small mammals and birds (carnivore)", "Least Concern", "The heaviest venomous snake in North America, with a rattle to warn off threats."),
    ("Gaboon Viper", "Bitis gabonica", "Reptile", "tropical rainforest", "sub-Saharan Africa", "small mammals and birds (carnivore)", "Least Concern", "Has the longest fangs of any venomous snake, up to 5 cm."),
    ("Bearded Dragon", "Pogona vitticeps", "Reptile", "arid woodland and desert", "Australia", "insects, greens, and fruit (omnivore)", "Least Concern", "Puffs out a spiny throat pouch, its 'beard', to look larger when threatened."),
    # --- Amphibians ---
    ("Golden Poison Frog", "Phyllobates terribilis", "Amphibian", "tropical rainforest floor", "the Pacific coast of Colombia", "ants, termites, and small insects (insectivore)", "Endangered", "One of the most toxic animals on Earth, though captive-bred frogs lose most of their toxicity."),
    ("Red-eyed Tree Frog", "Agalychnis callidryas", "Amphibian", "tropical rainforest canopy", "Central America", "insects (insectivore)", "Least Concern", "Its startling red eyes may briefly stun predators, giving it a chance to flee."),
    ("American Bullfrog", "Lithobates catesbeianus", "Amphibian", "ponds, lakes, and marshes", "eastern North America", "insects, small fish, and even small birds (carnivore)", "Least Concern", "Named for its deep, bellowing call, audible over long distances."),
    ("Axolotl", "Ambystoma mexicanum", "Amphibian", "freshwater lakes and canals", "the Xochimilco lake system near Mexico City", "small invertebrates (carnivore)", "Critically Endangered", "Retains its larval, gilled form for life and can regrow entire limbs."),
    ("Fire Salamander", "Salamandra salamandra", "Amphibian", "damp forest floor", "Europe", "insects, worms, and slugs (insectivore)", "Least Concern", "Bold black-and-yellow markings warn predators of toxins in its skin."),
    ("Eastern Newt", "Notophthalmus viridescens", "Amphibian", "ponds and moist woodland", "eastern North America", "insects and small invertebrates (insectivore)", "Least Concern", "Passes through a bright orange land-dwelling 'eft' stage before returning to water as an adult."),
    ("Cane Toad", "Rhinella marina", "Amphibian", "grassland and woodland edges", "native to Central and South America", "insects and small animals (omnivore)", "Least Concern", "Introduced to Australia to control pests, it became a major invasive species instead."),
    ("Chinese Giant Salamander", "Andrias davidianus", "Amphibian", "cool mountain streams", "China", "fish, crustaceans, and insects (carnivore)", "Critically Endangered", "The largest living amphibian, capable of growing well over a meter long."),
    ("Hellbender", "Cryptobranchus alleganiensis", "Amphibian", "clear, fast-flowing rivers", "eastern United States", "crayfish and small fish (carnivore)", "Near Threatened", "Breathes largely through its skin, which needs cool, oxygen-rich water."),
    ("Tomato Frog", "Dyscophus antongilii", "Amphibian", "swamp and lowland forest", "Madagascar", "insects and small invertebrates (insectivore)", "Least Concern", "Its bright red-orange color warns predators, and it secretes a sticky defensive substance."),
    # --- Fish & marine mammals ---
    ("Great White Shark", "Carcharodon carcharias", "Fish", "coastal and offshore ocean waters", "temperate and subtropical oceans worldwide", "seals, fish, and other marine animals (carnivore)", "Vulnerable", "Can detect a single drop of blood diluted in a huge volume of seawater."),
    ("Hammerhead Shark", "Sphyrna species", "Fish", "coastal and open ocean waters", "tropical and warm-temperate seas worldwide", "fish, squid, and rays (carnivore)", "Vulnerable", "Its wide, flattened head improves sensory detection and gives it excellent maneuverability."),
    ("Whale Shark", "Rhincodon typus", "Fish", "open tropical ocean", "tropical oceans worldwide", "plankton and small fish (filter feeder)", "Endangered", "The largest fish in the ocean, yet it feeds mostly on some of the smallest organisms."),
    ("Manta Ray", "Mobula birostris", "Fish", "open ocean and coastal reefs", "tropical and subtropical oceans worldwide", "plankton (filter feeder)", "Endangered", "Has one of the largest brain-to-body ratios of any fish."),
    ("Clownfish", "Amphiprion ocellaris", "Fish", "coral reefs", "the Indo-Pacific", "algae, plankton, and small invertebrates (omnivore)", "Least Concern", "Lives among sea anemone tentacles, protected by a mucus coating that resists the anemone's sting."),
    ("Lined Seahorse", "Hippocampus erectus", "Fish", "seagrass beds and coral reefs", "the western Atlantic", "small crustaceans (carnivore)", "Vulnerable", "Males, not females, carry and give birth to the young."),
    ("Bottlenose Dolphin", "Tursiops truncatus", "Mammal", "coastal and offshore ocean waters", "temperate and tropical oceans worldwide", "fish and squid (carnivore)", "Least Concern", "Uses echolocation to hunt and navigate, and individuals develop signature whistles like names."),
    ("Orca", "Orcinus orca", "Mammal", "oceans worldwide, from the tropics to polar seas", "all major oceans", "fish, seals, and other marine mammals (carnivore)", "Data Deficient", "The largest member of the dolphin family, living in tight-knit family pods."),
    ("West Indian Manatee", "Trichechus manatus", "Mammal", "shallow coastal waters and rivers", "the southeastern United States, Caribbean, and Gulf of Mexico", "seagrass and aquatic plants (herbivore)", "Vulnerable", "A gentle, slow-moving grazer sometimes called a 'sea cow'."),
    ("California Sea Lion", "Zalophus californianus", "Mammal", "coastal waters and rocky shores", "the eastern Pacific coast", "fish and squid (carnivore)", "Least Concern", "Highly trainable and vocal, often the star of marine mammal shows."),
    ("Harbor Seal", "Phoca vitulina", "Mammal", "coastal waters, bays, and estuaries", "the Northern Hemisphere", "fish and shellfish (carnivore)", "Least Concern", "Can dive up to 500 meters and hold its breath for over 30 minutes."),
    ("Walrus", "Odobenus rosmarus", "Mammal", "arctic sea ice and coastline", "the Arctic", "clams and other bottom-dwelling invertebrates (carnivore)", "Vulnerable", "Uses its long tusks to haul out onto ice and to spar for social rank."),
    ("Beluga Whale", "Delphinapterus leucas", "Mammal", "arctic and sub-arctic coastal waters", "the Arctic and sub-Arctic", "fish, squid, and crustaceans (carnivore)", "Least Concern", "Known as the 'canary of the sea' for its wide range of vocalizations."),
    ("Humpback Whale", "Megaptera novaeangliae", "Mammal", "oceans worldwide, from polar feeding grounds to tropical breeding waters", "all major oceans", "krill and small fish (filter feeder)", "Least Concern", "Males sing long, complex songs that can carry for many kilometers underwater."),
    ("Green Moray Eel", "Gymnothorax funebris", "Fish", "coral reefs and rocky coastlines", "the western Atlantic", "fish and crustaceans (carnivore)", "Least Concern", "Its yellow-tinted mucus coating over blue-grey skin gives it a green appearance."),
    # --- Invertebrates ---
    ("Honeybee", "Apis mellifera", "Invertebrate", "meadows, forests, and cultivated land", "worldwide (originally Europe, Africa, and Asia)", "nectar and pollen (nectarivore)", "Least Concern", "Communicates food locations to hive mates through a figure-eight 'waggle dance'."),
    ("Monarch Butterfly", "Danaus plexippus", "Invertebrate", "meadows and milkweed fields", "North America", "milkweed as larvae, nectar as adults (herbivore/nectarivore)", "Endangered", "Migrates up to 4,800 km between North America and central Mexico each year."),
    ("Praying Mantis", "Mantis religiosa", "Invertebrate", "grassland, garden, and shrubland", "widespread across temperate and tropical regions", "insects (carnivore)", "Least Concern", "Its triangular head can rotate nearly 180 degrees to track prey."),
    ("Emperor Scorpion", "Pandinus imperator", "Invertebrate", "tropical rainforest and savanna", "West Africa", "insects and small invertebrates (carnivore)", "Least Concern", "Glows blue-green under ultraviolet light, for reasons still debated by scientists."),
    ("Chilean Rose Tarantula", "Grammostola rosea", "Invertebrate", "arid scrubland and desert", "Chile and Argentina", "insects and small invertebrates (carnivore)", "Least Concern", "One of the most docile tarantula species, often kept as a first pet spider."),
    ("Giant Pacific Octopus", "Enteroctopus dofleini", "Invertebrate", "cold coastal waters and reefs", "the North Pacific", "crabs, shrimp, and fish (carnivore)", "Least Concern", "One of the most intelligent invertebrates, capable of solving puzzles and opening jars."),
    ("Moon Jellyfish", "Aurelia aurita", "Invertebrate", "coastal and open ocean waters", "oceans worldwide", "plankton (filter feeder)", "Least Concern", "Its translucent, saucer-shaped bell makes it one of the most recognizable jellyfish."),
    ("Ochre Sea Star", "Pisaster ochraceus", "Invertebrate", "rocky intertidal shores", "the Pacific coast of North America", "mussels and barnacles (carnivore)", "Least Concern", "A keystone species; removing it can dramatically reshape the intertidal community."),
    ("Atlantic Horseshoe Crab", "Limulus polyphemus", "Invertebrate", "shallow coastal waters and sandy beaches", "the eastern coast of North America", "worms and small mollusks (omnivore)", "Vulnerable", "More closely related to spiders and scorpions than to true crabs; its blue blood is prized in medical testing."),
    ("Garden Snail", "Cornu aspersum", "Invertebrate", "gardens, woodland, and grassland", "originally the Mediterranean, now worldwide", "leaves and plant matter (herbivore)", "Least Concern", "Carries its spiral shell for life, growing it larger as its body grows."),
]

COLUMNS = [
    "id", "name", "scientific_name", "category", "habitat", "region",
    "diet", "conservation_status", "fun_fact", "description",
]


def build_rows():
    rows = []
    for idx, (name, sci, category, habitat, region, diet, status, fact) in enumerate(ANIMALS, start=1):
        description = (
            f"{name} ({sci}) is a {category.lower()} that lives in {habitat}, "
            f"found in {region}. Diet: {diet}. "
            f"Conservation status: {status}. {fact}"
        )
        rows.append([idx, name, sci, category, habitat, region, diet, status, fact, description])
    return rows


def main():
    out_path = os.path.join(os.path.dirname(__file__), "animal_facts.csv")
    rows = build_rows()
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        writer.writerows(rows)
    print(f"Wrote {len(rows)} animal records to {out_path}")


if __name__ == "__main__":
    main()
