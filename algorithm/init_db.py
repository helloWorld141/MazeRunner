from web_main import db, MdfStrings

db.create_all()

db.session.add(MdfStrings(part1='FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',
                          part2='0000000000000000000000000000000000000000000000000000000000000000000000000000'))
db.session.add(MdfStrings(part1='FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',
                          part2='000000000400000001C800000000000700000000800000001F80000700000000020000000000'))
db.session.add(MdfStrings(part1='FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',
                          part2='000000000080010042038400000000000000010C000000000000021F84000800000000000400'))
db.session.add(MdfStrings(part1='FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',
                          part2='0000000000200400080010000070000000000000007E00FC0000000100000100000020000000'))
db.session.add(MdfStrings(part1='FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',
                          part2='00400080010000000000003F0400000000000001000401000000000380000000080010002000'))
db.session.add(MdfStrings(part1='FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',
                          part2='0400000800000201C00002000400080010202040408001000200040000380400000100000200'))
db.session.add(MdfStrings(part1='FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',
                          part2='000000000000BC01000200000408080010000000001F80210002000400080870000000000000'))
                          
db.session.commit()
