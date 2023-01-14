TAG=$1

if [ "$TAG" = "" ]; then
   TAG=0.1.0
fi

git push origin --delete $TAG
git tag -d $TAG
git tag $TAG
git push --tags
