import json

def split_parse_data(parse_data, train_filename, dev_filename, test_filename):
    test, dev, train= [], [], [] 
    for relation in parse_data:
        if relation['DocID'][4:6] == '23':
            test.append(relation)
        elif relation['DocID'][4:6] == '22':
            dev.append(relation)
        else:
            train.append(relation)
    relations_to_file(train, train_filename)
    relations_to_file(dev, dev_filename)
    relations_to_file(test, test_filename)


def relations_to_file(relations,filename):
    f = open(filename, 'a')
    for relation in relations:
        f.write(json.dumps(relation))
        f.write('\n')
    f.close()

if __name__ == '__main__':
    parse_raw = open('pdtb3.json').readlines()
    parse_data = [json.loads(o) for o in parse_raw]
    train_filename = 'train.json'
    dev_filename = 'dev.json'
    test_filename = 'test.json'
    split_parse_data(parse_data, train_filename, dev_filename, test_filename)
