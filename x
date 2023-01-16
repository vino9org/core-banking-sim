TAG=$1

if [ "$TAG" = "" ]; then
   TAG=0.1.4
fi

git push origin --delete $TAG
git tag -d $TAG
git tag $TAG
git push --tags
