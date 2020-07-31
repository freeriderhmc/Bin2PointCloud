# train.py

import pandas as pd
from tensorflow.keras.layers import SimpleRNN, Embedding, Dense, LSTM
from tensorflow.keras.models import Sequential
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.models import load_model
import utils
import matplotlib
import matplotlib.pyplot as plt
from sklearn import metrics

LABELS = [
    "NORMAL", 
    "LANE_CHANGE", 
    "TURN_LEFT"
]

def seperate_data(tracknum, cnt, span):
    rawdf = pd.read_csv('{}.csv'.format(tracknum), index_col=0)
    ansdf = pd.read_csv('{}_ans.csv'.format(tracknum), index_col = 0)
    temp = pd.merge(rawdf, ansdf, left_on="0", left_index = True,right_index = True, how='left').dropna(axis=0)
    data = []
    y_data = []
    for i in range(0, len(temp)-cnt):
        tmplist = []
        for j in range(i, cnt):
            tmplist.append(j)
        if(temp.iloc[i+cnt+span,5]==0):
            data.append(temp.iloc[tmplist,[0,1,3]].to_numpy())
            y_data.append(0)
        elif(temp.iloc[i+cnt+span,5]==1):
            data.append(temp.iloc[tmplist,[0,1,3]].to_numpy())
            y_data.append(1)
        elif(temp.iloc[i+cnt+span,5]==2):
            data.append(temp.iloc[tmplist,[0,1,3]].to_numpy())
            y_data.append(2)
        else:
            continue
    n_train = int(len(data) * 0.8)
    n_test = int(len(data) - n_train)
    
    X_test = data[n_train:]
    y_test = np.array(y_data[n_train:])
    X_train = data[:n_train]
    y_train = np.array(y_data[:n_train])
    
    return X_train, y_train, X_test, y_test

'''
X_train, y_train, X_test, y_test = seperate_data(0, 5, 3)
print(len(X_train))
X_train0, y_train0, X_test0, y_test0 = seperate_data(1, 5, 3)
X_train =np.append(X_train, X_train0, axis=0)
y_train = np.append(y_train,y_train0)
X_test =np.append(X_test, X_test0, axis=0)
y_test =np.append(y_test ,y_test0)
print(len(X_train))
print(len(y_train))
print(X_train)

model = Sequential()
# model.add(Embedding(3, 32)) # embedding vector 32 levels
model.add(LSTM(256, input_shape=(seq_len, 3))) # RNN cell hidden_size 32, SimpleRNN
model.add(Dense(3, activation='softmax')) #if classify->sigmoid

es = EarlyStopping(monitor='val_loss', mode='min', verbose=1, patience=4)
mc = ModelCheckpoint('best_model.h5', monitor='val_acc', mode='max', verbose=1, save_best_only=True)

#optimizer rmsprop
model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['acc'])
history = model.fit(X_train, y_train, epochs=100, batch_size=64, validation_split=0.2, callbacks=[es, mc])

loaded_model = load_model('best_model.h5')
print("\n test accuracy: %.4f" % (loaded_model.evaluate(X_test, y_test)[1]))

epochs = range(1, len(history.history['acc']) + 1)
plt.plot(epochs, history.history['loss'])
plt.plot(epochs, history.history['val_loss'])
plt.title('model loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'val'], loc='upper left')
plt.show()
'''
# Input Data 
training_data_count = len(X_train)
test_data_count = len(X_test)
n_steps = len(X_train[0]) #number of timestamp
n_input = len(X_train[0][0])  # how many input parameters per timestamp

print(training_data_count)
print(test_data_count)
print(n_steps)
print(n_input)

# LSTM Neural Network's internal structure
n_hidden = 32 # Hidden layer num of features
n_classes = 3


# Training 
learning_rate = 0.01 #
lambda_loss_amount = 0.0015 #
training_iters = training_data_count * 300  # Loop 300 times on the dataset
batch_size = 8 
display_iter = 1000  # show test set accuracy during training

# shape, normalization
print("(X shape, y shape, every X's mean, every X's standard deviation)")
print(X_test.shape, y_test.shape, np.mean(X_test), np.std(X_test))

# Graph input/output
x = tf.placeholder(tf.float32, [None, n_steps, n_input])
y = tf.placeholder(tf.float32, [None, n_classes])

# Graph weights
weights = {
    'hidden': tf.Variable(tf.random_normal([n_input, n_hidden])), # Hidden layer weights
    'out': tf.Variable(tf.random_normal([n_hidden, n_classes], mean=1.0))
}
biases = {
    'hidden': tf.Variable(tf.random_normal([n_hidden])),
    'out': tf.Variable(tf.random_normal([n_classes]))
}

pred = utils.LSTM_RNN(x, weights, biases)

# Loss, optimizer and evaluation
l2 = lambda_loss_amount * sum(
    tf.nn.l2_loss(tf_var) for tf_var in tf.trainable_variables()
) # L2 loss prevents this overkill neural network to overfit the data
cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels=y, logits=pred)) + l2 # Softmax loss
optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cost) # Adam Optimizer

correct_pred = tf.equal(tf.argmax(pred,1), tf.argmax(y,1))
accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32))

test_losses = []
test_accuracies = []
train_losses = []
train_accuracies = []

# Launch the graph
sess = tf.InteractiveSession(config=tf.ConfigProto(log_device_placement=True))
init = tf.global_variables_initializer()
sess.run(init)

# Perform Training steps with "batch_size" amount of example data at each loop
step = 1
while step * batch_size <= training_iters:
    batch_xs =         utils.extract_batch_size(X_train, step, batch_size)
    batch_ys = utils.one_hot(extract_batch_size(y_train, step, batch_size))

    # Fit training using batch data
    _, loss, acc = sess.run(
        [optimizer, cost, accuracy],
        feed_dict={
            x: batch_xs, 
            y: batch_ys
        }
    )
    train_losses.append(loss)
    train_accuracies.append(acc)
    
    # Evaluate network only at some steps for faster training: 
    if (step*batch_size % display_iter == 0) or (step == 1) or (step * batch_size > training_iters):
        
        
        print("Training iter #" + str(step*batch_size) + \
              ":   Batch Loss = " + "{:.6f}".format(loss) + \
              ", Accuracy = {}".format(acc))
        
        # Evaluation on the test set
        loss, acc = sess.run(
            [cost, accuracy], 
            feed_dict={
                x: X_test,
                y: one_hot(y_test)
            }
        )
        test_losses.append(loss)
        test_accuracies.append(acc)
        print("PERFORMANCE ON TEST SET: " + \
              "Batch Loss = {}".format(loss) + \
              ", Accuracy = {}".format(acc))

    step += 1

print("Optimization Done")

# Accuracy for test data

one_hot_predictions, accuracy, final_loss = sess.run(
    [pred, accuracy, cost],
    feed_dict={
        x: X_test,
        y: one_hot(y_test)
    }
)

test_losses.append(final_loss)
test_accuracies.append(accuracy)

print("FINAL RESULT: " + \
      "Batch Loss = {}".format(final_loss) + \
      ", Accuracy = {}".format(accuracy))

font = {
    'family' : 'Bitstream Vera Sans',
    'weight' : 'bold',
    'size'   : 18
}
matplotlib.rc('font', **font)

width = 12
height = 12
plt.figure(figsize=(width, height))

indep_train_axis = np.array(range(batch_size, (len(train_losses)+1)*batch_size, batch_size))
plt.plot(indep_train_axis, np.array(train_losses),     "b--", label="Train losses")
plt.plot(indep_train_axis, np.array(train_accuracies), "g--", label="Train accuracies")

indep_test_axis = np.append(
    np.array(range(batch_size, len(test_losses)*display_iter, display_iter)[:-1]),
    [training_iters]
)
plt.plot(indep_test_axis, np.array(test_losses),     "b-", label="Test losses")
plt.plot(indep_test_axis, np.array(test_accuracies), "g-", label="Test accuracies")

plt.title("Training session's progress over iterations")
plt.legend(loc='upper right', shadow=True)
plt.ylabel('Training Progress (Loss or Accuracy values)')
plt.xlabel('Training iteration')

plt.show()

# Results
predictions = one_hot_predictions.argmax(1)

print("Testing Accuracy: {}%".format(100*accuracy))

print("")
print("Precision: {}%".format(100*metrics.precision_score(y_test, predictions, average="weighted")))
print("Recall: {}%".format(100*metrics.recall_score(y_test, predictions, average="weighted")))
print("f1_score: {}%".format(100*metrics.f1_score(y_test, predictions, average="weighted")))

print("")
print("Confusion Matrix:")
confusion_matrix = metrics.confusion_matrix(y_test, predictions)
print(confusion_matrix)
normalised_confusion_matrix = np.array(confusion_matrix, dtype=np.float32)/np.sum(confusion_matrix)*100

print("")
print("Confusion matrix (normalised to % of total test data):")
print(normalised_confusion_matrix)
print("Note: training and testing data is not equally distributed amongst classes, ")
print("so it is normal that more than a 6th of the data is correctly classifier in the last category.")

# Plot Results: 
width = 12
height = 12
plt.figure(figsize=(width, height))
plt.imshow(
    normalised_confusion_matrix, 
    interpolation='nearest', 
    cmap=plt.cm.rainbow
)
plt.title("Confusion matrix \n(normalised to % of total test data)")
plt.colorbar()
tick_marks = np.arange(n_classes)
plt.xticks(tick_marks, LABELS, rotation=90)
plt.yticks(tick_marks, LABELS)
plt.tight_layout()
plt.ylabel('True label')
plt.xlabel('Predicted label')
plt.show()
