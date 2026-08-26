import { Minio } from 'minio-js';
import csv from 'csvtojson'
import X2js from 'x2js'
// import {Minio} from 'tz-minio-upload_beta';

// const minioClient = new Minio({
//   endPoint: 'YOUR_MINIO_ENDPOINT',
//   port: YOUR_MINIO_PORT,
//   useSSL: true, // 根据实际情况选择是否启用SSL
//   accessKey: 'YOUR_MINIO_ACCESS_KEY',
//   secretKey: 'YOUR_MINIO_SECRET_KEY'
// });
//测试用
// const port = '9000'
// const endPoint = 's3.rustfs.com'
// const accessKey = 'T2O9IVPX19A8PGX7WA9K';
// const secretKey = '2LaQlPhS766W+8Nfs+f5ZikRWhwoUsnP1wf+2NPl';
//自己的
const port = 31900
const endPoint = '10.0.33.151'
const accessKey = 'RdwWh6LMS9qEj83qKwL8';
const secretKey = 'jQ5mxwzw4lOZqBfAQ1ZCiXM1jIh1sMWGNWcphu2S';
const minioClient = new Minio.Client({
    endPoint,
    port,
    useSSL: false,
    accessKey: accessKey,
    secretKey: secretKey,
    // accessKeyId: accessKey,
    // secretAccessKey: secretKey,
    // s3ForcePathStyle: true, // 必须设置为true以使用路径样式
    // signatureVersion: 'v4',
    // sessionToken: sessionToken,
});
export const uploadFile = (bucketName, objectName, file) => {
    return new Promise((resolve, reject) => {
        minioClient.putObject(bucketName, objectName, file, (err, etag) => {
            if (err) {
                return reject(err);
            }
            resolve(etag);
        });
    });
};

export const getListObjectFile = (bucketName, prefix = '') => {
    return new Promise((resolve, reject) => {
        const stream = minioClient.listObjectsV2(bucketName, prefix, true, '')
        let data = []
        stream.on('data', function(obj) {
            data.push(obj)
                // let x2js = new X2js()
                // let json = x2js.xml2js(obj)
                // console.log(json,'newjson')
        })
        stream.on('end', function(obj) {
            resolve(data)
        })
        stream.on('error', function(err) {
            return reject(err);
        })
    })
};

export const getObjectDownloadFile = (bucketName, fileName) => {
    return new Promise((resolve, reject) => {
        let data = '';
        minioClient.getObject(bucketName, fileName, (err, stream) => {
            if (err) {
                return reject(err);
            }
            stream.on('data', chunk => {
                data += chunk.toString();
            });
            stream.on('end', async() => {
                try {
                    const jsonArray = await csv().fromString(data);
                    resolve({ raw: data, parsed: jsonArray });
                    // resolve(jsonArray);
                } catch (parseErr) {
                    reject(parseErr);
                }
            });
            stream.on('error', err => {
                reject(err);
            });
        });
    })

};

export const readMultipleFiles = async(bucketName, fileNames) => {
    const results = [];
    for (const fileName of fileNames) {
        try {
            const fileData = await getObjectDownloadFile(bucketName, fileName);
            results.push(fileData);
        } catch (error) {
            console.error(`Error reading file ${fileName}:`, error);
        }
    }
    return results;
};