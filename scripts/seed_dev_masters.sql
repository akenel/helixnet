-- Dev-only: seed a real hall of masters into borrowhood.bh_user so the dispatcher + Legends wall
-- are properly testable (LEGEND tier, synthetic @borrowhood.local emails -> matches the board filter).
-- Idempotent: ON CONFLICT (email) DO NOTHING. No 'Kenel' names (board stays family-free).
INSERT INTO bh_user
  (id, keycloak_id, email, display_name, slug, workshop_name, tagline, bio,
   account_status, badge_tier, notify_telegram, notify_email, created_at, updated_at)
SELECT gen_random_uuid(), gen_random_uuid()::text, v.email, v.name, v.slug, v.workshop, v.tagline, v.bio,
       'ACTIVE'::accountstatus, 'LEGEND'::badgetier, false, false, now(), now()
FROM (VALUES
  ('nikola.tesla@borrowhood.local','Nikola Tesla','nikola-tesla','Tesla Coil Works','Inventor of alternating current','Serbian-American inventor and electrical engineer who shaped modern power.'),
  ('thomas.edison@borrowhood.local','Thomas Edison','thomas-edison','Menlo Park Lab','Prolific inventor and tinkerer','American inventor of the practical light bulb and the phonograph.'),
  ('james.watt@borrowhood.local','James Watt','james-watt','The Steam Shop','Engineer of the steam engine','Scottish engineer whose steam engine powered the industrial revolution.'),
  ('leonardo.davinci@borrowhood.local','Leonardo da Vinci','leonardo-davinci','The Renaissance Studio','Painter, engineer, anatomist','Italian polymath of the High Renaissance, painter of the Mona Lisa.'),
  ('frida.kahlo@borrowhood.local','Frida Kahlo','frida-kahlo','Casa Azul','Painter of the inner world','Mexican painter known for vivid self-portraits and folk style.'),
  ('akira.kurosawa@borrowhood.local','Akira Kurosawa','akira-kurosawa','The Film Atelier','Master filmmaker','Japanese director of Seven Samurai and Rashomon.'),
  ('albert.einstein@borrowhood.local','Albert Einstein','albert-einstein','The Thought Lab','Theory of relativity','German-born physicist who reshaped our view of space and time.'),
  ('marie.curie@borrowhood.local','Marie Curie','marie-curie','The Radium Bench','Pioneer of radioactivity','Physicist and chemist, first person to win two Nobel Prizes.'),
  ('aristotle@borrowhood.local','Aristotle','aristotle','The Lyceum Walk','Philosopher of everything','Greek philosopher and polymath, student of Plato.'),
  ('sun.tzu@borrowhood.local','Sun Tzu','sun-tzu','The War Room','Strategist of the Art of War','Ancient Chinese general and author of The Art of War.'),
  ('napoleon.bonaparte@borrowhood.local','Napoleon Bonaparte','napoleon-bonaparte','The Campaign Tent','Strategist and emperor','French military and political leader of great ambition.'),
  ('william.shakespeare@borrowhood.local','William Shakespeare','william-shakespeare','The Globe Desk','Playwright and poet','English playwright, the Bard of Avon.'),
  ('jane.austen@borrowhood.local','Jane Austen','jane-austen','The Writing Parlour','Novelist of manners and wit','English novelist of Pride and Prejudice.'),
  ('homer@borrowhood.local','Homer','homer','The Epic Hearth','Poet of the Iliad and Odyssey','Ancient Greek epic poet.'),
  ('andrew.carnegie@borrowhood.local','Andrew Carnegie','andrew-carnegie','The Steel Counting House','Industrialist and philanthropist','Scottish-American steel magnate who gave his fortune away.'),
  ('coco.chanel@borrowhood.local','Coco Chanel','coco-chanel','The Maison','Fashion entrepreneur','French couturier who founded the Chanel brand.'),
  ('julia.child@borrowhood.local','Julia Child','julia-child','The Test Kitchen','Teacher of French cooking','American chef who brought French cuisine to home cooks.'),
  ('auguste.escoffier@borrowhood.local','Auguste Escoffier','auguste-escoffier','The Grand Kitchen','Codifier of haute cuisine','French chef who modernized the professional kitchen.'),
  ('galileo.galilei@borrowhood.local','Galileo Galilei','galileo-galilei','The Observatory Tower','Father of observational astronomy','Italian astronomer who turned the telescope to the heavens.'),
  ('zheng.he@borrowhood.local','Zheng He','zheng-he','The Treasure Fleet','Admiral and explorer','Chinese mariner who led vast treasure voyages.'),
  ('ferdinand.magellan@borrowhood.local','Ferdinand Magellan','ferdinand-magellan','The Navigation Deck','Circumnavigator','Portuguese explorer whose expedition first circled the globe.'),
  ('ludwig.beethoven@borrowhood.local','Ludwig van Beethoven','ludwig-beethoven','The Composition Room','Composer of symphonies','German composer who bridged classical and romantic eras.'),
  ('wolfgang.mozart@borrowhood.local','Wolfgang Amadeus Mozart','wolfgang-mozart','The Conservatory','Prodigy composer','Austrian composer of the classical era.'),
  ('hippocrates@borrowhood.local','Hippocrates','hippocrates','The Healing Hall','Father of medicine','Ancient Greek physician, namesake of the Hippocratic Oath.'),
  ('florence.nightingale@borrowhood.local','Florence Nightingale','florence-nightingale','The Lamp Ward','Founder of modern nursing','English social reformer and founder of modern nursing.')
) AS v(email, name, slug, workshop, tagline, bio)
ON CONFLICT (email) DO NOTHING;
